import streamlit as st
import pandas as pd
import sys
import html as _html_lib
from pathlib import Path
from urllib.parse import quote as _url_quote
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, str(Path(__file__).parent))
from scrapers import oda_search, meny_search
from scrapers.kassal import search as kassal_search, is_configured as kassal_configured
from scrapers.kassal_stores import fetch_physical_stores, postnummer_to_coords, nearest_stores
import os
import sqlite3
import db
import auth
from normalize import normalize_search_term, check_threshold
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent / ".env", override=True)

st.set_page_config(page_title="Prissammenligning", page_icon="🛒", layout="wide")

_user = auth.require_login()
_user_db_id = db.ensure_user(_user["sub"], _user["email"], _user["name"])
_ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "")
_is_admin = bool(_ADMIN_EMAIL) and _user.get("email") == _ADMIN_EMAIL

# Ikonhandlinger fra HTML-kortvisning (WL/liste-toggle via URL-params)
if "card_action" in st.query_params:
    _ca = st.query_params.get("card_action", "")
    _cn = st.query_params.get("card_name", "")
    _cv = st.query_params.get("card_var", "")
    _cq = st.query_params.get("card_q", "")
    if _ca == "wl" and _cn:
        _wl_n = f"{_cn} {_cv}".strip() if _cv else _cn
        _existing_wl = {w["original_name"].lower() for w in db.get_watchlist(_user_db_id)}
        if _wl_n.lower() in _existing_wl or _cn.lower() in _existing_wl:
            db.remove_from_watchlist(_user_db_id, _wl_n)
        else:
            db.add_to_watchlist(_user_db_id, _wl_n, "sale", None)
    elif _ca == "li" and _cn:
        _all_lists = db.get_shopping_lists(_user_db_id)
        _on_any = any(
            item["original_name"].lower() == _cn.lower()
            for lst in _all_lists
            for item in db.get_shopping_list_items(lst["id"])
        )
        if _on_any:
            for lst in _all_lists:
                for item in db.get_shopping_list_items(lst["id"]):
                    if item["original_name"].lower() == _cn.lower():
                        db.remove_shopping_list_item(item["id"])
        elif _all_lists:
            db.add_to_shopping_list(_all_lists[0]["id"], _cn)
        else:
            _new_lid = db.create_shopping_list(_user_db_id, "Handleliste")
            db.add_to_shopping_list(_new_lid, _cn)
    if _cq:
        st.session_state.last_query = _cq
        st.session_state.auto_search = True
        st.session_state.search_results = None
    st.query_params.clear()

STORES = {"Oda": oda_search, "Meny": meny_search}
ONLINE_STORES = {"Oda", "Meny"}
KASSAL_STORE_LABEL = "🏪 Fysiske butikker (via Kassal)"


# ---------------------------------------------------------------------------
# Hjelpefunksjoner
# ---------------------------------------------------------------------------

def _check_watchlist_on_search(results: dict) -> None:
    for store, products in results.items():
        if store == "OBS 📰":
            continue
        for p in products:
            name = p.get("name") if isinstance(p, dict) else None
            variant = p.get("variant") if isinstance(p, dict) else None
            price = p.get("price") if isinstance(p, dict) else None
            if not name or price is None:
                continue
            # Sjekk både med og uten variant — watchlist kan være lagret begge veier
            wl_name = f"{name} {variant}".strip() if variant else name
            wl_items = db.get_watchlist_by_name(wl_name) or db.get_watchlist_by_name(name)
            if not wl_items:
                continue
            avg = db.get_avg_price_by_name(wl_name, store, days=30) or price
            for item in wl_items:
                if check_threshold(item, price, avg):
                    db.mark_watchlist_triggered(item["id"], price, store)


def _best_product(products: list, preferred_volume: str | None):
    if not products:
        return None
    if not preferred_volume:
        return products[0]
    pv = preferred_volume.lower()
    for p in products:
        v = (p.get("variant") if isinstance(p, dict) else getattr(p, "variant", "")) or ""
        if pv in v.lower() or v.lower() in pv:
            return p
    return products[0]


def run_search(query: str, limit: int) -> tuple[dict, dict]:
    results, errors = {}, {}
    with ThreadPoolExecutor(max_workers=len(STORES)) as executor:
        futures = {executor.submit(fn, query, limit): name for name, fn in STORES.items()}
        for future in as_completed(futures):
            name = futures[future]
            try:
                results[name] = future.result()
            except Exception as e:
                errors[name] = str(e)
                results[name] = []
    obs = db.search_obs(query)
    if obs:
        results["OBS 📰"] = obs
    return results, errors


def run_kassal_search(query: str, limit: int = 15) -> dict[str, list]:
    """Hent resultater fra Kassal.app gruppert per butikknavn. Lagrer priser til price_history."""
    if not kassal_configured():
        return {}
    products = kassal_search(query, limit=limit)
    grouped: dict[str, list] = {}
    for p in products:
        key = p.store_name or "Kassal"
        grouped.setdefault(key, []).append(p.to_dict())
        try:
            db.record_price(
                p.name, key, p.price,
                unit_price=p.unit_price, volume=p.variant, ean=p.ean,
            )
        except Exception:
            pass
    return grouped


def _market_badge(price: float, all_prices: list[float]) -> str | None:
    """Returner badge-tekst hvis prisen avviker >5% fra gjennomsnittet."""
    if len(all_prices) < 2:
        return None
    avg = sum(all_prices) / len(all_prices)
    if avg == 0:
        return None
    pct = (price - avg) / avg * 100
    if pct < -10:
        return f"🟢 {abs(pct):.0f}% under snitt"
    if pct < -5:
        return f"🟢 {abs(pct):.0f}% under snitt"
    if pct > 10:
        return f"🔴 {pct:.0f}% over snitt"
    return None


def _card_html(
    name: str,
    variant: str | None,
    price: float | None,
    unit_price: str | None,
    image_url: str | None,
    url: str | None,
    market_badge: str | None,
    on_wl: bool,
    on_list: bool,
    store: str,
    store_color: str,
    query: str = "",
    obs_status: str | None = None,
) -> str:
    ne = _html_lib.escape(name or "")
    ve = _html_lib.escape(variant or "")
    ie = _html_lib.escape(image_url or "")
    ue = _html_lib.escape(url or "")
    nq = _url_quote(name or "")
    vq = _url_quote(variant or "")
    qq = _url_quote(query or "")
    wl_href = f"?card_action=wl&card_name={nq}&card_var={vq}&card_q={qq}"
    li_href = f"?card_action=li&card_name={nq}&card_q={qq}"

    wl_color = "#ef4444" if on_wl else "#c4c4c4"
    wl_icon = "♥" if on_wl else "♡"
    li_color = "#22c55e" if on_list else "#c4c4c4"
    li_icon = "✓" if on_list else "+"

    ibtn = (
        "display:inline-flex;align-items:center;justify-content:center;"
        "width:32px;height:32px;border-radius:50%;"
        "background:rgba(255,255,255,0.96);"
        "box-shadow:0 1px 5px rgba(0,0,0,0.18);"
        "text-decoration:none;line-height:1;"
    )

    if image_url and isinstance(image_url, str):
        img = f'<img src="{ie}" style="position:absolute;inset:0;width:100%;height:100%;object-fit:contain;" loading="lazy">'
    else:
        img = '<div style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center;color:#d1d5db;font-size:3rem;">🛒</div>'

    price_s = (
        f'<span style="font-size:1.3rem;font-weight:700;color:#111827;">kr {price:.2f}</span>'
        if price is not None
        else '<span style="font-size:12px;color:#9ca3af;font-style:italic;">Ingen prisdata</span>'
    )
    up_s = f' <span style="font-size:11px;color:#3b82f6;font-weight:500;">{_html_lib.escape(unit_price)}</span>' if unit_price else ""

    badge_s = ""
    if market_badge:
        bc = "#16a34a" if "under" in market_badge else "#dc2626"
        badge_s = f'<div style="font-size:11px;color:{bc};margin-top:3px;">{_html_lib.escape(market_badge)}</div>'
    if obs_status:
        badge_s += f'<div style="font-size:11px;color:#6b7280;margin-top:3px;">{_html_lib.escape(obs_status)}</div>'

    view_s = f'<a href="{ue}" target="_blank" style="font-size:11px;color:#9ca3af;text-decoration:none;">Vis i butikk ↗</a>' if url else ""

    store_pill = (
        f'<span style="position:absolute;bottom:8px;left:8px;background:{store_color};'
        f'color:white;font-size:9px;font-weight:700;padding:2px 7px;border-radius:9999px;'
        f'letter-spacing:0.04em;opacity:0.88;">{_html_lib.escape(store)}</span>'
    )

    return (
        '<div style="background:white;border-radius:12px;'
        'box-shadow:0 2px 10px rgba(0,0,0,0.08);overflow:hidden;margin-bottom:10px;'
        "font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;\">"

        '<div style="position:relative;width:100%;padding-top:100%;background:#f8f9fa;">'
        + img
        + '<div style="position:absolute;top:8px;right:8px;display:flex;flex-direction:column;gap:6px;z-index:2;">'
        + f'<a href="{wl_href}" style="{ibtn}font-size:17px;color:{wl_color};" title="{"Fjern varsel" if on_wl else "Varsle meg"}">{wl_icon}</a>'
        + f'<a href="{li_href}" style="{ibtn}font-size:20px;color:{li_color};font-weight:600;" title="{"Fjern fra liste" if on_list else "Legg i liste"}">{li_icon}</a>'
        + "</div>"
        + store_pill
        + "</div>"

        + '<div style="padding:10px 12px 12px;">'
        + f'<div style="font-size:13px;font-weight:600;color:#111827;line-height:1.35;margin-bottom:2px;">{ne}</div>'
        + f'<div style="font-size:11px;color:#9ca3af;margin-bottom:7px;">{ve}</div>'
        + f'<div style="display:flex;align-items:baseline;flex-wrap:wrap;gap:4px;">{price_s}{up_s}</div>'
        + badge_s
        + (f'<div style="margin-top:7px;">{view_s}</div>' if view_s else "")
        + "</div>"
        + "</div>"
    )


def _user_lists() -> list[dict]:
    return db.get_shopping_lists(_user_db_id)


def _all_item_names() -> set[str]:
    names: set[str] = set()
    for lst in _user_lists():
        for item in db.get_shopping_list_items(lst["id"]):
            names.add(item["original_name"].lower())
    return names


# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------

_DEFAULTS: dict = {
    "section": "søk",
    "active_list_id": None,
    "search_results": None,
    "search_errors": {},
    "last_query": "",
    "liste_resultater": None,
    "show_admin": False,
    "wl_add_name": None,
    "bulk_add_feedback": None,
    "kassal_results": {},
    "product_detail": None,  # {name, variant, store, price}
    "join_feedback": None,   # melding etter ?join=<token>
    "auto_search": False,
    "kassal_stores_cache": None,
}

# Håndter ?join=<token> — automatisk innmelding i delt liste
_join_token = st.query_params.get("join")
if _join_token:
    _join_list = db.get_list_by_share_token(_join_token)
    if _join_list:
        if _join_list["user_id"] == _user_db_id:
            st.session_state.join_feedback = ("info", "Dette er din egen liste.")
        else:
            db.add_list_member(_join_list["id"], _user_db_id)
            st.session_state.join_feedback = ("success", f"Du er nå med i listen **{_join_list['name']}**!")
            st.session_state.section = "handlelister"
            st.session_state.active_list_id = _join_list["id"]
    else:
        st.session_state.join_feedback = ("warning", "Ugyldig eller utløpt invitasjonslenke.")
    st.query_params.clear()
for _k, _v in _DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v


# ---------------------------------------------------------------------------
# Admin-panel
# ---------------------------------------------------------------------------

def _admin_panel() -> None:
    st.title("🔧 Admin")
    conn = sqlite3.connect(db.DB_PATH)
    conn.row_factory = sqlite3.Row

    def _count(table: str) -> int:
        return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]

    def _adf(sql: str, params: tuple = ()) -> pd.DataFrame:
        rows = conn.execute(sql, params).fetchall()
        return pd.DataFrame([dict(r) for r in rows]) if rows else pd.DataFrame()

    st.subheader("Oversikt")
    acols = st.columns(6)
    for col, (label, table) in zip(acols, [
        ("Brukere", "user"), ("Produkter", "product"), ("Normnavn", "normal"),
        ("Prishistorikk", "product_price_history"), ("Watchlist", "watchlist"), ("Sesjoner", "session"),
    ]):
        col.metric(label, _count(table))

    st.divider()
    st.subheader("Brukere")
    udf = _adf("SELECT id, email, name, created_at FROM user ORDER BY created_at DESC")
    if not udf.empty:
        st.dataframe(udf, use_container_width=True, hide_index=True)
    else:
        st.caption("Ingen")

    st.subheader("Handlelister")
    sldf = _adf(
        """SELECT sl.id, u.email, sl.name, sl.created_at, COUNT(sli.id) as items
           FROM shopping_list sl
           JOIN user u ON sl.user_id = u.id
           LEFT JOIN shopping_list_item sli ON sli.list_id = sl.id
           WHERE sl.archived = 0
           GROUP BY sl.id ORDER BY sl.created_at DESC"""
    )
    if not sldf.empty:
        st.dataframe(sldf, use_container_width=True, hide_index=True)
    else:
        st.caption("Ingen")

    st.divider()
    st.subheader("Rådata")
    all_tables = [r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()]
    chosen = st.selectbox("Velg tabell", all_tables, key="admin_table_select")
    row_limit = st.slider("Maks rader", 10, 500, 50, key="admin_row_limit")
    if chosen:
        tdf = _adf(f"SELECT * FROM {chosen} ORDER BY rowid DESC LIMIT ?", (row_limit,))
        if not tdf.empty:
            st.dataframe(tdf, use_container_width=True, hide_index=True)
            st.caption(f"{len(tdf)} rader (maks {row_limit})")
        else:
            st.caption("Tom tabell")

    st.divider()
    st.subheader("Vedlikehold")
    mc1, mc2, mc3 = st.columns(3)
    with mc1:
        if st.button("Slett utlopte sesjoner (>30 dager)", type="secondary"):
            conn.execute("DELETE FROM session WHERE created_at < date('now', '-30 days')")
            conn.commit()
            st.success("Slettet")
    with mc2:
        null_count = conn.execute(
            "SELECT COUNT(*) FROM normal WHERE auto_name IS NULL"
        ).fetchone()[0]
        total_count = conn.execute("SELECT COUNT(*) FROM normal").fetchone()[0]
        st.metric("Normal uten auto_name", f"{null_count} / {total_count}")
    with mc3:
        if st.button("🔄 Kjør auto-normalisering (force)", type="secondary",
                     help="Overskriv alle auto_name med ny normalize-logikk"):
            from tasks import run_auto_normalize
            n = run_auto_normalize(force=True)
            st.success(f"✓ {n} produktnavn oppdatert")

    st.divider()
    st.subheader("EAN-dekning")

    ean_rows = conn.execute(
        """SELECT s.name as butikk,
                  COUNT(*) as totalt,
                  SUM(CASE WHEN p.ean IS NOT NULL THEN 1 ELSE 0 END) as med_ean
           FROM product p JOIN store s ON p.store_id = s.id
           GROUP BY s.name ORDER BY s.name"""
    ).fetchall()
    if ean_rows:
        import pandas as pd
        ean_df = pd.DataFrame([dict(r) for r in ean_rows])
        ean_df["dekning"] = ean_df.apply(
            lambda r: f"{r['med_ean']}/{r['totalt']} ({100*r['med_ean']//r['totalt']}%)"
            if r["totalt"] else "–", axis=1
        )
        st.dataframe(ean_df[["butikk", "totalt", "med_ean", "dekning"]],
                     use_container_width=True, hide_index=True)
    else:
        st.caption("Ingen produkter i DB ennå")

    st.markdown("**Kryssbutikk-treff (samme EAN, flere butikker)**")
    cross_rows = conn.execute(
        """SELECT p.ean,
                  GROUP_CONCAT(s.name, ' · ') as butikker,
                  COUNT(DISTINCT p.store_id) as antall_butikker,
                  MIN(p.original_name) as produktnavn
           FROM product p JOIN store s ON p.store_id = s.id
           WHERE p.ean IS NOT NULL
           GROUP BY p.ean
           HAVING COUNT(DISTINCT p.store_id) > 1
           ORDER BY antall_butikker DESC, p.ean
           LIMIT 100"""
    ).fetchall()
    if cross_rows:
        cross_df = pd.DataFrame([dict(r) for r in cross_rows])
        st.dataframe(cross_df[["ean", "produktnavn", "butikker", "antall_butikker"]],
                     use_container_width=True, hide_index=True)
        st.caption(f"{len(cross_df)} EAN-koder funnet i flere butikker")
    else:
        st.caption("Ingen kryssbutikk-treff ennå — søk etter produkter for å bygge opp data")

    conn.close()


# ---------------------------------------------------------------------------
# Varslingsliste-popover og seksjon
# ---------------------------------------------------------------------------

def _varsle_meg_popover(name: str, price: float, key_suffix: str) -> None:
    on_wl = db.is_on_watchlist(_user_db_id, name)
    label = "⭐ Varslet" if on_wl else "⭐ Varsle meg"
    with st.popover(label):
        if on_wl:
            st.caption(f"**{name.capitalize()}** er allerede i varslingslisten.")
            if st.button("Fjern varsel", key=f"wl_rm_s_{key_suffix}"):
                db.remove_from_watchlist(_user_db_id, name)
                st.rerun()
        else:
            st.markdown(f"**Varsle meg om {name.capitalize()} når...**")
            options = [
                "Prisen er på tilbud (anbefalt)",
                f"Prisen er under X kr  (nå: {price:.0f} kr)",
                "Prisen er mer enn X% billigere enn snitt",
            ]
            choice = st.radio("Terskel", options, key=f"wl_type_{key_suffix}", label_visibility="collapsed")
            threshold_value = None
            if "under X kr" in choice:
                threshold_value = st.number_input(
                    "Grensepris (kr)", min_value=0.1, value=round(price * 0.9, 1),
                    key=f"wl_val_{key_suffix}"
                )
            elif "X%" in choice:
                threshold_value = st.number_input(
                    "Prosent lavere", min_value=1, max_value=80, value=10,
                    key=f"wl_pct_{key_suffix}"
                )
            type_map = {
                options[0]: "sale",
                options[1]: "absolute",
                options[2]: "relative",
            }
            if st.button("Lagre varsel", key=f"wl_save_{key_suffix}", type="primary"):
                db.add_to_watchlist(_user_db_id, name, type_map[choice], threshold_value)
                st.success("✓ Varsel lagret")


def _show_varslingsliste() -> None:
    watchlist = db.get_watchlist(_user_db_id)

    triggered = [w for w in watchlist if w["status"] == "triggered"]
    waiting   = [w for w in watchlist if w["status"] == "waiting"]
    ignored   = [w for w in watchlist if w["status"] not in ("triggered", "waiting")]

    st.title("⭐ Varslingsliste")

    # Legg til vare fra varslingslisten i en handleliste
    if st.session_state.wl_add_name:
        pname = st.session_state.wl_add_name
        st.info(f"Legg **{pname.capitalize()}** i en handleliste:")
        lists = _user_lists()
        if not lists:
            nl = st.text_input("Ny liste", value="Handleliste", key="wl_new_list")
            if st.button("Opprett og legg til", type="primary"):
                lid = db.create_shopping_list(_user_db_id, nl.strip() or "Handleliste")
                db.add_to_shopping_list(lid, pname)
                st.session_state.wl_add_name = None
                st.rerun()
        else:
            chosen = st.selectbox("Velg liste", [l["name"] for l in lists], key="wl_list_sel")
            if st.button("Legg til i liste", type="primary"):
                lid = next(l["id"] for l in lists if l["name"] == chosen)
                db.add_to_shopping_list(lid, pname)
                st.session_state.wl_add_name = None
                st.rerun()
        if st.button("Avbryt"):
            st.session_state.wl_add_name = None
            st.rerun()
        st.stop()

    if not watchlist:
        st.info("Ingen varsler ennå. Søk etter et produkt og klikk ⭐ Varsle meg.")
        return

    def _threshold_desc(w: dict) -> str:
        t, v = w["threshold_type"], w["threshold_value"]
        if t == "absolute":
            return f"under {v:.0f} kr"
        if t == "relative":
            return f"> {v:.0f}% billigere enn snitt"
        return "på tilbud"

    if triggered:
        st.subheader(f"🟢 Truffet ({len(triggered)})")
        for w in triggered:
            c1, c2, c3 = st.columns([5, 2, 2])
            c1.markdown(
                f"**{w['original_name'].capitalize()}**  \n"
                f"_{_threshold_desc(w)}_"
            )
            c2.markdown(
                f"**{w['triggered_price']:.2f} kr**  \n"
                f"{w['triggered_store']}"
            )
            with c3:
                if st.button("➕ Legg i liste", key=f"wl_trig_add_{w['id']}"):
                    st.session_state.wl_add_name = w["original_name"]
                    db.reset_watchlist_item(w["id"])
                    st.rerun()
                if st.button("Ignorer", key=f"wl_trig_ign_{w['id']}"):
                    db.reset_watchlist_item(w["id"])
                    st.rerun()

    if waiting:
        st.subheader(f"🟡 Venter ({len(waiting)})")
        for w in waiting:
            c1, c2 = st.columns([8, 1])
            c1.markdown(
                f"**{w['original_name'].capitalize()}**  \n"
                f"_{_threshold_desc(w)}_"
            )
            if c2.button("✕", key=f"wl_wait_rm_{w['id']}", use_container_width=True):
                db.remove_from_watchlist(_user_db_id, w["original_name"])
                st.rerun()

    if ignored:
        with st.expander(f"⚫ Inaktive ({len(ignored)})"):
            for w in ignored:
                c1, c2 = st.columns([8, 1])
                c1.markdown(f"**{w['original_name'].capitalize()}**")
                if c2.button("✕", key=f"wl_ign_rm_{w['id']}", use_container_width=True):
                    db.remove_from_watchlist(_user_db_id, w["original_name"])
                    st.rerun()

    st.divider()
    _prishistorikk_expander("vl_")


# ---------------------------------------------------------------------------
# Produkt-handlinger: 🔔 📋 👁️ 🔍  (brukes i kortvisning og detaljvisning)
# ---------------------------------------------------------------------------

def _produkt_handlinger(
    name: str,
    price: float,
    url: str | None,
    variant: str | None,
    key_suffix: str,
    wl_names: set | None = None,
    already_added: set | None = None,
    is_obs: bool = False,
) -> None:
    wl_name = f"{name} {variant}".strip() if variant else name
    if wl_names is None:
        wl_names = {w["original_name"].lower() for w in db.get_watchlist(_user_db_id)}
    if already_added is None:
        already_added = _all_item_names()
    on_wl = wl_name.lower() in wl_names or name.lower() in wl_names
    on_list = name.lower() in already_added

    c1, c2, c3, c4 = st.columns(4)

    # 🔔 Varsling
    if not is_obs:
        with c1.popover("🔔" if on_wl else "🔕", help="Varsling"):
            if on_wl:
                st.caption(f"**{wl_name.capitalize()}** er på varslingslisten.")
                if st.button("Fjern varsel", key=f"bell_rm_{key_suffix}"):
                    db.remove_from_watchlist(_user_db_id, wl_name)
                    st.rerun()
            else:
                st.markdown(f"**Varsle meg om {name.capitalize()} når...**")
                opts = [
                    "Prisen er på tilbud (anbefalt)",
                    f"Prisen er under X kr  (nå: {price:.0f} kr)",
                    "Prisen er mer enn X% billigere enn snitt",
                ]
                choice = st.radio("Terskel", opts, key=f"bell_type_{key_suffix}", label_visibility="collapsed")
                tval = None
                if "under X kr" in choice:
                    tval = st.number_input("Grensepris (kr)", min_value=0.1, value=round(price * 0.9, 1), key=f"bell_val_{key_suffix}")
                elif "X%" in choice:
                    tval = st.number_input("Prosent lavere", min_value=1, max_value=80, value=10, key=f"bell_pct_{key_suffix}")
                ttype = "sale" if "tilbud" in choice else ("absolute" if "under X" in choice else "relative")
                if st.button("Lagre varsel", key=f"bell_save_{key_suffix}", type="primary"):
                    db.add_to_watchlist(_user_db_id, wl_name, ttype, tval)
                    st.success("✓ Varsel lagret")

    # 📋 Handleliste
    list_icon = "✅" if on_list else "📋"
    with c2.popover(list_icon, help="Handleliste"):
        if on_list:
            st.caption(f"**{name.capitalize()}** er allerede på handlelisten.")
        else:
            lists = _user_lists()
            if not lists:
                st.info("Ingen lister ennå.")
                nl = st.text_input("Opprett ny liste", value="Handleliste", key=f"li_nl_{key_suffix}")
                if st.button("Opprett og legg til", key=f"li_cnl_{key_suffix}", type="primary"):
                    lid = db.create_shopping_list(_user_db_id, nl.strip() or "Handleliste")
                    db.add_to_shopping_list(lid, name)
                    st.rerun()
            else:
                chosen = st.selectbox("Velg liste", [l["name"] for l in lists], key=f"li_sel_{key_suffix}")
                qty = st.number_input("Antall", min_value=1, value=1, key=f"li_qty_{key_suffix}")
                if st.button("Legg til", key=f"li_add_{key_suffix}", type="primary"):
                    lid = next(l["id"] for l in lists if l["name"] == chosen)
                    db.add_to_shopping_list(lid, name, quantity=int(qty))
                    st.success(f"✓ Lagt til i {chosen}")

    # 👁️ Vis i butikk
    if url and not is_obs:
        c3.link_button("👁️", url, help="Vis i butikk")

    # 🔍 Søk på dette produktet
    if c4.button("🔍", key=f"resok_{key_suffix}", help="Søk på dette produktet"):
        st.session_state.last_query = name
        st.session_state.search_results = None
        st.session_state.auto_search = True
        st.session_state.section = "søk"
        st.rerun()


# ---------------------------------------------------------------------------
# "Legg i liste"-popover (brukes i søkeresultater)
# ---------------------------------------------------------------------------

def _legg_til_popover(name: str, key_suffix: str) -> None:
    with st.popover("➕ Legg i liste"):
        lists = _user_lists()
        if not lists:
            st.info("Ingen lister ennå.")
            nl = st.text_input("Opprett ny liste", value="Handleliste", key=f"nl_{key_suffix}")
            if st.button("Opprett og legg til", key=f"cnl_{key_suffix}", type="primary"):
                lid = db.create_shopping_list(_user_db_id, nl.strip() or "Handleliste")
                db.add_to_shopping_list(lid, name)
                st.rerun()
        else:
            list_names = [l["name"] for l in lists]
            chosen = st.selectbox("Velg liste", list_names, key=f"lsel_{key_suffix}")
            qty = st.number_input("Antall", min_value=1, value=1, key=f"qty_{key_suffix}")
            if st.button("Legg til", key=f"ladd_{key_suffix}", type="primary"):
                lid = next(l["id"] for l in lists if l["name"] == chosen)
                db.add_to_shopping_list(lid, name, quantity=int(qty))
                st.success(f"✓ Lagt til i {chosen}")


# ---------------------------------------------------------------------------
# Seksjon: Produktdetalj (STEG 12)
# ---------------------------------------------------------------------------

def _show_product_detail() -> None:
    import re as _re

    pd_info = st.session_state.product_detail
    name: str = pd_info["name"]
    variant: str = pd_info.get("variant") or ""
    orig_store: str = pd_info.get("store") or ""

    if st.button("← Tilbake til søk"):
        st.session_state.product_detail = None
        st.rerun()

    display_name = f"{name} · {variant}" if variant else name
    st.title(display_name)
    if orig_store:
        st.caption(f"Opprinnelig fra: {orig_store}")

    query = normalize_search_term(name)
    _show_fysiske = db.get_user_setting(_user_db_id, "vis_fysiske_butikker", "0") == "1"

    with st.spinner("Henter priser fra alle butikker …"):
        results, _ = run_search(query, 10)
        kassal = run_kassal_search(query, limit=20) if _show_fysiske else {}

    # Tokens fra produktnavnet som brukes for relevansfiltrering.
    # Krav: minst ett token (≥4 tegn) fra det opprinnelige produktnavnet
    # må finnes i resultattnavnet for å unngå off-topic treff.
    _name_tokens = [t.lower() for t in _re.split(r'\W+', name) if len(t) >= 4]

    def _is_relevant(result_name: str) -> bool:
        if not _name_tokens:
            return True
        rl = result_name.lower()
        return any(tok in rl for tok in _name_tokens)

    def _vol_matches(result_variant: str) -> bool:
        if not variant:
            return True
        rv = (result_variant or "").lower().replace(" ", "")
        sv = variant.lower().replace(" ", "")
        return sv in rv or rv in sv

    all_prices: list[dict] = []
    seen: set[tuple] = set()  # (butikk_key, pris) for dedup innad i kilde

    for store, prods in results.items():
        if store == "OBS 📰":
            continue
        for p in prods:
            pd_dict = p.to_dict() if hasattr(p, "to_dict") else p
            price = pd_dict.get("price")
            result_name = pd_dict.get("name") or ""
            if price is None or not _is_relevant(result_name):
                continue
            key = (store.lower(), round(float(price), 2))
            if key in seen:
                continue
            seen.add(key)
            all_prices.append({
                "Butikk": store,
                "Produkt": result_name or name,
                "Mengde": pd_dict.get("variant") or "",
                "Pris (kr)": float(price),
                "Per enhet": pd_dict.get("unit_price") or "",
                "_online": True,
            })

    for store, prods in kassal.items():
        # Ikke vis Kassal-data for butikker vi allerede har direkte scraper-data fra
        if store in ONLINE_STORES:
            continue
        for p in prods:
            price = p.get("price")
            result_name = p.get("name") or ""
            if price is None or not _is_relevant(result_name):
                continue
            key = (store.lower(), round(float(price), 2))
            if key in seen:
                continue
            seen.add(key)
            all_prices.append({
                "Butikk": f"🏪 {store}",
                "Produkt": result_name or name,
                "Mengde": p.get("variant") or "",
                "Pris (kr)": float(price),
                "Per enhet": p.get("unit_price") or "",
                "_online": False,
            })

    # Del i "samme volum" og "andre størrelser"
    same_vol = sorted(
        [p for p in all_prices if _vol_matches(p["Mengde"])],
        key=lambda x: x["Pris (kr)"],
    )
    other_vol = sorted(
        [p for p in all_prices if not _vol_matches(p["Mengde"])],
        key=lambda x: x["Pris (kr)"],
    )

    def _show_price_table(rows: list[dict]) -> None:
        df_p = pd.DataFrame([{k: v for k, v in r.items() if not k.startswith("_")} for r in rows])
        st.dataframe(
            df_p,
            column_config={"Pris (kr)": st.column_config.NumberColumn(format="%.2f kr")},
            use_container_width=True,
            hide_index=True,
        )

    if not same_vol and not other_vol:
        st.info("Ingen priser funnet for dette produktet.")
    else:
        focus = same_vol if same_vol else other_vol
        cheapest = focus[0]
        st.success(
            f"💰 Billigst: **{cheapest['Butikk']}** — kr {cheapest['Pris (kr)']:.2f}"
            + (f"  ·  {cheapest['Per enhet']}" if cheapest["Per enhet"] else "")
        )

        if same_vol:
            vol_label = f" ({variant})" if variant else ""
            st.subheader(f"Priser{vol_label}")
            _show_price_table(same_vol)
        else:
            _show_price_table(other_vol)

        if other_vol and same_vol:
            with st.expander(f"Andre størrelser ({len(other_vol)} resultater)"):
                _show_price_table(other_vol)

    # Handlinger
    st.divider()
    wl_name = display_name if variant else name
    ref_price = same_vol[0]["Pris (kr)"] if same_vol else (other_vol[0]["Pris (kr)"] if other_vol else pd_info.get("price", 0.0))
    _produkt_handlinger(name, ref_price, None, variant, f"det_{name[:12]}")

    # Prishistorikk
    st.divider()
    st.subheader("📈 Prishistorikk")
    history = db.get_price_history(name, days=90)
    if history:
        df_h = pd.DataFrame(history)
        df_h["recorded_at"] = pd.to_datetime(df_h["recorded_at"]).dt.floor("D")
        df_pivot = (
            df_h.pivot_table(index="recorded_at", columns="store", values="price", aggfunc="mean")
            .sort_index()
        )
        st.line_chart(df_pivot, height=250)
        with st.expander("Vis rådata"):
            st.dataframe(
                df_h[["recorded_at", "store", "price", "unit_price"]].rename(
                    columns={"recorded_at": "Dato", "store": "Butikk", "price": "Pris", "unit_price": "Per enhet"}
                ).sort_values("Dato", ascending=False),
                use_container_width=True, hide_index=True,
            )
    else:
        st.caption("Ingen prishistorikk ennå — søk priser for en handleliste for å bygge opp data.")


# ---------------------------------------------------------------------------
# Seksjon: Søk
# ---------------------------------------------------------------------------

def _show_search() -> None:
    if st.session_state.product_detail:
        _show_product_detail()
        return

    st.title("🔍 Søk")

    with st.form("search_form"):
        col1, col2 = st.columns([6, 1])
        with col1:
            query = st.text_input(
                "Søk etter produkt",
                value=st.session_state.last_query,
                placeholder="f.eks. havregryn, smør, egg...",
            )
        with col2:
            st.write("")
            submitted = st.form_submit_button("Søk", type="primary", use_container_width=True)
        limit = 5

    # Auto-søk utløst fra 🔍-knapp på produktkort
    if not submitted and st.session_state.get("auto_search") and st.session_state.last_query:
        submitted = True
        query = st.session_state.last_query
        st.session_state.auto_search = False

    if st.session_state.bulk_add_feedback:
        fb = st.session_state.bulk_add_feedback
        fc, bc = st.columns([3, 1])
        fc.success(f"✓ {fb['count']} vare(r) lagt til i **{fb['list_name']}**")
        if bc.button("Åpne liste →", use_container_width=True):
            st.session_state.section = "handlelister"
            st.session_state.active_list_id = fb["list_id"]
            st.session_state.bulk_add_feedback = None
            st.rerun()

    if submitted:
        st.session_state.bulk_add_feedback = None
        if not query.strip():
            st.warning("Skriv inn et søkeord.")
            st.stop()
        _show_fysiske = db.get_user_setting(_user_db_id, "vis_fysiske_butikker", "0") == "1"
        _norm_query = normalize_search_term(query.strip())
        with st.spinner(f'Søker etter "{query.strip()}" ...'):
            results, errors = run_search(_norm_query, int(limit))
            kassal_results = run_kassal_search(_norm_query) if _show_fysiske else {}
        converted: dict = {}
        for store, products in results.items():
            if store == "OBS 📰":
                converted[store] = products
            else:
                converted[store] = [p.to_dict() if hasattr(p, "to_dict") else p for p in products]
        _check_watchlist_on_search(converted)
        st.session_state.search_results = converted
        st.session_state.search_errors = errors
        st.session_state.last_query = query.strip()
        st.session_state.kassal_results = kassal_results

    if st.session_state.search_results is None:
        return

    q = st.session_state.last_query
    results = st.session_state.search_results
    errors = st.session_state.search_errors
    already_added = _all_item_names()

    _wl_items = db.get_watchlist(_user_db_id)
    _wl_names = {w["original_name"].lower() for w in _wl_items}

    # --- Kombinert tabell ---
    def _on_wl(p: dict, store: str) -> str:
        if store == "OBS 📰":
            return ""
        name = (p.get("name") or "").lower()
        variant = p.get("variant") or ""
        with_variant = f"{name} {variant}".strip().lower()
        return "⭐" if (name in _wl_names or with_variant in _wl_names) else ""

    kassal_res = st.session_state.get("kassal_results", {})
    all_rows = [
        {
            "⭐": _on_wl(p, store),
            "Butikk": store,
            "Produkt": p.get("product_name") if store == "OBS 📰" else p.get("name"),
            "Mengde": p.get("volume") if store == "OBS 📰" else p.get("variant") or "",
            "Pris (kr)": p["price"],
            "Per enhet": p.get("unit_price") or "",
        }
        for store, prods in results.items()
        for p in prods
    ] + [
        {
            "⭐": _on_wl(kp, kstore),
            "Butikk": kstore,
            "Produkt": kp.get("name"),
            "Mengde": kp.get("variant") or "",
            "Pris (kr)": kp["price"],
            "Per enhet": kp.get("unit_price") or "",
        }
        for kstore, kprods in kassal_res.items()
        for kp in kprods
        if kstore not in ONLINE_STORES
    ]

    if all_rows:
        st.subheader(f'Resultater for "{q}"')

        f1, f2 = st.columns([3, 2])
        with f1:
            available_stores = sorted({r["Butikk"] for r in all_rows})
            valgte = st.multiselect(
                "Vis butikker", available_stores, default=available_stores, key="filter_butikker"
            )
        with f2:
            sorter = st.selectbox(
                "Sorter etter", ["Pris (kr)", "Produkt", "Butikk"], key="filter_sortering"
            )

        df = pd.DataFrame(all_rows)
        if valgte:
            df = df[df["Butikk"].isin(valgte)]
        df = df.sort_values(sorter, na_position="last").reset_index(drop=True)

        selection = st.dataframe(
            df,
            column_config={
                "⭐": st.column_config.TextColumn("⭐", width="small"),
                "Pris (kr)": st.column_config.NumberColumn(format="%.2f kr"),
            },
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="multi-row",
        )

        selected_rows = selection.selection.rows if selection else []
        if len(selected_rows) == 1:
            row_sel = df.iloc[selected_rows[0]]
            if row_sel.get("Butikk") != "OBS 📰" and row_sel.get("Produkt"):
                ta1, ta2 = st.columns([2, 2])
                if ta1.button("🔍 Vis detaljer →", type="secondary", key="btn_detail"):
                    st.session_state.product_detail = {
                        "name": row_sel["Produkt"],
                        "variant": row_sel.get("Mengde") or "",
                        "store": row_sel.get("Butikk") or "",
                        "price": row_sel.get("Pris (kr)") or 0.0,
                    }
                    st.rerun()
                if ta2.button("🔍 Nytt søk", type="secondary", key="btn_resok"):
                    st.session_state.last_query = row_sel["Produkt"]
                    st.session_state.auto_search = True
                    st.session_state.search_results = None
                    st.rerun()
        if selected_rows:
            lists = _user_lists()
            ba1, ba2, ba3 = st.columns([2, 3, 2])
            with ba2:
                if lists:
                    target = st.selectbox(
                        "Legg til i", [l["name"] for l in lists], key="bulk_list_target"
                    )
                else:
                    target = st.text_input("Ny liste", value="Handleliste", key="bulk_new_list")
            with ba1:
                if st.button(f"➕ Legg til valgte ({len(selected_rows)})", type="primary"):
                    if not lists:
                        lid = db.create_shopping_list(_user_db_id, target or "Handleliste")
                    else:
                        lid = next(l["id"] for l in lists if l["name"] == target)
                    added = 0
                    for row_idx in selected_rows:
                        pname = df.iloc[row_idx]["Produkt"]
                        if pname and pname.lower() not in already_added:
                            db.add_to_shopping_list(lid, pname)
                            added += 1
                    st.session_state.bulk_add_feedback = {
                        "list_name": target, "list_id": lid, "count": added
                    }
                    st.rerun()
            with ba3:
                if st.button(f"⭐ Varsle valgte ({len(selected_rows)})", type="secondary"):
                    added_wl = 0
                    for row_idx in selected_rows:
                        row_df = df.iloc[row_idx]
                        pname = row_df.get("Produkt")
                        pstore = row_df.get("Butikk", "")
                        pprice = row_df.get("Pris (kr)", 0.0)
                        if pname and pstore != "OBS 📰" and pname.lower() not in _wl_names:
                            db.add_to_watchlist(_user_db_id, pname, "sale", None)
                            added_wl += 1
                    if added_wl:
                        st.success(f"✓ {added_wl} varsel(er) lagt til")
                        st.rerun()

    st.divider()

    # Samle alle priser for markedspris-kontekst
    _all_search_prices: list[float] = [
        p.get("price") for prods in results.values()
        for p in prods if isinstance(p, dict) and p.get("price") is not None
    ]

    # Fase 1 — global CSS-reset: shadow-kort, rene kolonner
    st.markdown("""<style>
[data-testid="stVerticalBlockBorderWrapper"] {
  border: none !important;
  border-radius: 12px !important;
  box-shadow: 0 2px 10px rgba(0,0,0,0.07) !important;
  transition: box-shadow .18s ease !important;
}
[data-testid="stVerticalBlockBorderWrapper"]:hover {
  box-shadow: 0 4px 18px rgba(0,0,0,0.12) !important;
}
</style>""", unsafe_allow_html=True)

    # --- Per-butikk kolonner ---
    _STORE_COLORS = {"Oda": "#005b96", "Meny": "#c0021b", "OBS 📰": "#d97706"}
    _KASSAL_CHAINS = {
        "MENY": "#c0021b", "Rema 1000": "#e63329", "Rema": "#e63329",
        "Kiwi": "#00843d", "Coop Extra": "#004f9e", "Coop Obs": "#004f9e",
        "Spar": "#e5231b", "Bunnpris": "#003087",
    }
    # Bygg samlet butikk-struktur: online scrapers + Kassal (uten duplikater)
    all_store_data: dict[str, list] = {s: p for s, p in results.items()}
    for ks, kp in kassal_res.items():
        if ks not in ONLINE_STORES:
            all_store_data[ks] = kp
            # Sett farge for kjente kjeder
            for chain, color in _KASSAL_CHAINS.items():
                if chain.lower() in ks.lower() and ks not in _STORE_COLORS:
                    _STORE_COLORS[ks] = color

    stores_to_show = list(all_store_data.keys())
    cols = st.columns(max(len(stores_to_show), 1))
    for col, store in zip(cols, stores_to_show):
        with col:
            color = _STORE_COLORS.get(store, "#444444")
            st.markdown(
                f'<h3 style="color:{color};margin-bottom:0.25rem">{store}</h3>',
                unsafe_allow_html=True,
            )
            if store in errors:
                st.error(f"Feil: {errors[store]}")
            elif not all_store_data.get(store):
                st.info("Ingen resultater")
            else:
                for i, p in enumerate(all_store_data[store]):
                    is_obs = store == "OBS 📰"
                    name = p.get("product_name") if is_obs else p.get("name")
                    price = p.get("price")
                    unit_price = p.get("unit_price") if not is_obs else None
                    variant = p.get("volume") if is_obs else p.get("variant")
                    url = p.get("url") if not is_obs else None
                    valid_to = p.get("valid_to") if is_obs else None
                    image_url = p.get("image_url")
                    wl_name = f"{name} {variant}".strip() if variant else name

                    if name:
                        on_wl = wl_name.lower() in _wl_names or name.lower() in _wl_names
                        on_list = name.lower() in already_added
                        mbadge = _market_badge(price, _all_search_prices) if price is not None and not is_obs else None
                        obs_st = None
                        if is_obs and valid_to:
                            from datetime import date as _date
                            obs_st = "⏰ Utløpt" if valid_to < _date.today().isoformat() else f"✅ Gyldig til {valid_to}"
                        st.markdown(
                            _card_html(name, variant, price, unit_price, image_url, url,
                                       mbadge, on_wl, on_list, store, color,
                                       st.session_state.get("last_query", ""), obs_st),
                            unsafe_allow_html=True,
                        )

    # Kassal-resultater er integrert i tabellen og per-butikk-kolonner ovenfor
    st.divider()
    _prishistorikk_expander("sok_")


# ---------------------------------------------------------------------------
# Seksjon: Handlelister — prissammenligning
# ---------------------------------------------------------------------------

def _search_list_prices(items: list[dict]) -> None:
    vis_fysiske = db.get_user_setting(_user_db_id, "vis_fysiske_butikker", "0") == "1"
    use_kassal = vis_fysiske and kassal_configured()
    active_stores = list(STORES.keys()) + (["Kassal"] if use_kassal else [])

    rows = []
    totals = {s: 0.0 for s in active_stores}
    mangler: dict[str, list[str]] = {s: [] for s in active_stores}
    trends: dict[str, dict[str, dict]] = {}

    with st.spinner("Søker priser for alle varer ..."):
        for item in items:
            vare = item["original_name"]
            qty = item.get("quantity", 1)
            note = item.get("note") or ""
            search_query = normalize_search_term(f"{vare} {note}".strip() if note else vare)
            vare_label = f"{vare.capitalize()} ({note})" if note else vare.capitalize()
            res, _ = run_search(search_query, 3)
            row: dict = {"Vare": vare_label, "_navn": vare, "Antall": qty}
            for store_name in STORES:
                prods = res.get(store_name, [])
                best = _best_product(prods, None)
                if best:
                    price = best.price if hasattr(best, "price") else best["price"]
                    unit_price = (
                        getattr(best, "unit_price", None)
                        or (best.get("unit_price") if isinstance(best, dict) else None)
                    )
                    variant = (
                        getattr(best, "variant", None)
                        or (best.get("variant") if isinstance(best, dict) else None)
                    )
                    best_name = (
                        getattr(best, "name", None)
                        or (best.get("name") if isinstance(best, dict) else None)
                        or vare
                    )
                    row[store_name] = price
                    row[f"{store_name} (enhet)"] = unit_price or ""
                    row[f"{store_name} (variant)"] = variant or ""
                    row[f"{store_name} (produkt)"] = f"{best_name}" + (f" · {variant}" if variant else "")
                    totals[store_name] += price * qty
                    db.record_price(vare, store_name, price, unit_price=unit_price, volume=variant)
                    t = db.get_price_trend(vare, store_name, volume=variant)
                    if t and t["delta"] < -0.01:
                        trends.setdefault(vare, {})[store_name] = t
                else:
                    row[store_name] = None
                    row[f"{store_name} (enhet)"] = ""
                    mangler[store_name].append(vare)

            # Kassal: billigste pris på tvers av alle fysiske butikker
            if use_kassal:
                kassal_prods = kassal_search(search_query, limit=8)
                if kassal_prods:
                    best_k = min(kassal_prods, key=lambda p: p.price)
                    row["Kassal"] = best_k.price
                    row["Kassal (enhet)"] = best_k.unit_price or ""
                    row["Kassal (variant)"] = best_k.variant or ""
                    row["Kassal (produkt)"] = f"{best_k.name} · {best_k.store_name}"
                    totals["Kassal"] += best_k.price * qty
                else:
                    row["Kassal"] = None
                    row["Kassal (enhet)"] = ""
                    mangler["Kassal"].append(vare)

            rows.append(row)

    st.session_state.liste_resultater = {
        "rows": rows, "totals": totals, "mangler": mangler, "trends": trends,
        "stores": active_stores,
    }


def _show_liste_resultater() -> None:
    lr = st.session_state.liste_resultater
    rows, totals = lr["rows"], lr["totals"]
    mangler, trends = lr["mangler"], lr.get("trends", {})
    active_stores = lr.get("stores", list(STORES.keys()))

    for vare, store_trends in trends.items():
        for store_name, t in store_trends.items():
            st.success(
                f"↓ Prisfall! **{vare.capitalize()}** er billigere på {store_name}: "
                f"kr {t['current']:.2f} (var kr {t['previous']:.2f}, spart kr {abs(t['delta']):.2f})"
            )

    st.subheader("Prissammenligning")

    optimal_total = 0.0
    store_best_sums = {s: 0.0 for s in active_stores}
    rows_display = []
    for row in rows:
        qty = row.get("Antall", 1)
        prices = {s: row[s] for s in active_stores if row.get(s) is not None}
        if prices:
            best = min(prices, key=prices.get)
            store_best_sums[best] += prices[best] * qty
            optimal_total += prices[best] * qty
        else:
            best = "—"
        product_name = row.get("_navn", row["Vare"])
        display_row = {k: v for k, v in row.items() if k != "_navn"}
        for s in active_stores:
            variant = row.get(f"{s} (variant)") or None
            trend = db.get_price_trend(product_name, s, volume=variant)
            if trend and abs(trend["delta"]) > 0.01:
                if trend["delta"] > 0:
                    display_row[f"{s} trend"] = f"🔴 ↑ {trend['delta']:+.2f} kr"
                else:
                    display_row[f"{s} trend"] = f"🟢 ↓ {trend['delta']:+.2f} kr"
            else:
                display_row[f"{s} trend"] = ""
        rows_display.append({**display_row, "Billigst": best})

    col_config: dict = {}
    for s in active_stores:
        col_config[s] = st.column_config.NumberColumn(s, format="%.2f kr")
        col_config[f"{s} (enhet)"] = st.column_config.TextColumn(f"{s}/enhet", width="small")
        col_config[f"{s} (variant)"] = None
        col_config[f"{s} (produkt)"] = st.column_config.TextColumn(f"{s} produkt", width="medium")
        col_config[f"{s} trend"] = st.column_config.TextColumn(f"{s} ↑↓", width="small")

    st.dataframe(
        pd.DataFrame(rows_display), column_config=col_config,
        use_container_width=True, hide_index=True
    )

    st.subheader("Oppsummering")
    m_cols = st.columns(1 + len(active_stores))
    m_cols[0].metric(
        "🏆 Optimal sum", f"kr {optimal_total:.2f}",
        help="Billigste alternativ per vare på tvers av butikker"
    )
    for i, store in enumerate(active_stores, 1):
        delta = totals.get(store, 0) - optimal_total
        missing = mangler.get(store, [])
        m_cols[i].metric(
            store,
            f"kr {store_best_sums.get(store, 0):.2f}",
            delta=(
                f"Alt på {store}: kr {totals.get(store, 0):.2f} (+kr {delta:.2f})"
                if delta > 0.01
                else f"Alt på {store}: kr {totals.get(store, 0):.2f}"
            ),
            delta_color="off",
        )
        if missing:
            m_cols[i].caption(
                f"⚠️ {len(missing)} vare(r) ikke funnet her — totalen er ufullstendig"
            )
    for store, missing in mangler.items():
        if missing:
            st.warning(f"{store}: ingen treff for: {', '.join(missing)}")

    # --- Optimal handleplan ---
    _PLAN_COLORS = {"Oda": "#005b96", "Meny": "#c0021b", "Kassal": "#2d6a2d"}
    st.subheader("🗺️ Optimal handleplan")
    st.caption("Hvilke varer du bør kjøpe hvor for å minimere totalkostnad.")
    plan: dict[str, list[str]] = {}
    for row in rows:
        prices = {s: row[s] for s in active_stores if row.get(s) is not None}
        if not prices:
            continue
        cheapest_store = min(prices, key=prices.get)
        product_label = (
            row.get(f"{cheapest_store} (produkt)")
            or row.get("Vare", "")
        )
        qty = row.get("Antall", 1)
        qty_str = f" × {qty}" if qty > 1 else ""
        price_str = f" — kr {prices[cheapest_store]:.2f}"
        plan.setdefault(cheapest_store, []).append(f"{product_label}{qty_str}{price_str}")

    if plan:
        plan_cols = st.columns(len(plan))
        for col, (store, items) in zip(plan_cols, plan.items()):
            with col:
                with st.container(border=True):
                    color = _PLAN_COLORS.get(store, "#444")
                    st.markdown(
                        f'<b style="color:{color}">{store}</b>', unsafe_allow_html=True
                    )
                    for item in items:
                        st.markdown(f"- {item}")
    else:
        st.info("Ikke nok prisdata til å lage handleplan.")


# ---------------------------------------------------------------------------
# Seksjon: Handlelister
# ---------------------------------------------------------------------------

def _show_handlelister() -> None:
    active_id = st.session_state.active_list_id

    if active_id is None:
        st.title("🛒 Mine handlelister")

        # --- Familie-seksjon ---
        user_families = db.get_user_families(_user_db_id)
        if user_families:
            for fam in user_families:
                fam_id = fam["id"]
                is_fam_owner = fam["my_role"] == "owner"
                with st.expander(
                    f"👨‍👩‍👧 Familie: **{fam['name']}** · kode: `{fam['invite_code']}`"
                ):
                    members = db.get_family_members(fam_id)
                    st.caption(
                        "Alle familiemedlemmer ser hverandres handlelister automatisk."
                    )
                    st.markdown(f"**Medlemmer ({len(members)}):**")
                    for m in members:
                        crown = " 👑" if m["role"] == "owner" else ""
                        st.caption(f"{m['name'] or m['email']}{crown}")
                    st.divider()
                    if is_fam_owner:
                        if st.button(
                            "🗑️ Slett familie",
                            key=f"del_family_{fam_id}",
                            type="secondary",
                            help="Alle mister tilgang til hverandres lister",
                        ):
                            db.delete_family(fam_id)
                            st.rerun()
                    else:
                        if st.button("Forlat familie", key=f"leave_family_{fam_id}", type="secondary"):
                            db.leave_family(fam_id, _user_db_id)
                            st.rerun()
        else:
            fc1, fc2 = st.columns(2)
            with fc1:
                with st.expander("👨‍👩‍👧 Opprett familie"):
                    fam_name = st.text_input(
                        "Familienavn", placeholder="f.eks. Familie Berntsen", key="new_family_name"
                    )
                    if st.button("Opprett", key="create_family_btn") and fam_name.strip():
                        fam = db.create_family(fam_name.strip(), _user_db_id)
                        st.success(f"Familie opprettet! Del koden: **{fam['invite_code']}**")
                        st.rerun()
            with fc2:
                with st.expander("🔑 Bli med i familie"):
                    fam_code = st.text_input(
                        "Delingskode", placeholder="f.eks. A3F7B2", key="join_family_code"
                    )
                    if st.button("Bli med", key="join_family_btn") and fam_code.strip():
                        found_fam = db.get_family_by_invite_code(fam_code.strip())
                        if not found_fam:
                            st.warning("Ugyldig kode — sjekk at du har skrevet riktig.")
                        else:
                            db.join_family(found_fam["id"], _user_db_id)
                            st.success(f"Du er nå med i familie **{found_fam['name']}**!")
                            st.rerun()

        st.divider()

        with st.expander("➕ Ny liste"):
            nl = st.text_input(
                "Navn på listen", placeholder="f.eks. Ukeshandel", key="new_list_name"
            )
            if st.button("Opprett liste", key="create_list_btn") and nl.strip():
                db.create_shopping_list(_user_db_id, nl.strip())
                st.rerun()

        lists = _user_lists()
        if not lists:
            st.info(
                "Ingen handlelister ennå. Opprett en ny liste ovenfor, "
                "eller søk etter varer (🔍 Søk) og legg dem til."
            )
            return

        for lst in lists:
            role = lst.get("my_role", "owner")
            is_owner = role == "owner"
            if role == "owner":
                icon, owner_note = "", ""
            elif role == "member":
                icon = "👥 "
                owner_note = f" _(delt av {lst.get('owner_name', '?')})_"
            else:  # family
                icon = "👨‍👩‍👧 "
                fam_label = lst.get("family_name") or ""
                owner_note = f" _({lst.get('owner_name', '?')}" + (f" · {fam_label}" if fam_label else "") + ")_"
            c1, c2, c3 = st.columns([7, 1, 1])
            c1.markdown(f"**{icon}{lst['name']}**{owner_note} — {lst['item_count']} varer")
            if c2.button("Åpne", key=f"open_{lst['id']}", use_container_width=True):
                st.session_state.active_list_id = lst["id"]
                st.session_state.liste_resultater = None
                st.rerun()
            if is_owner:
                if c3.button("🗑️", key=f"del_{lst['id']}", use_container_width=True, help="Slett liste"):
                    db.delete_shopping_list(lst["id"])
                    st.rerun()
            elif role == "member":
                if c3.button("✕", key=f"leave_{lst['id']}", use_container_width=True, help="Forlat liste"):
                    db.remove_list_member(lst["id"], _user_db_id)
                    st.rerun()
            # family-lister: ingen knapp — forlat familien for å fjerne tilgang

    else:
        lists = _user_lists()
        list_info = next((l for l in lists if l["id"] == active_id), None)
        if list_info is None:
            st.session_state.active_list_id = None
            st.rerun()

        list_name = list_info["name"]

        if st.button("← Tilbake til lister"):
            st.session_state.active_list_id = None
            st.session_state.liste_resultater = None
            st.rerun()

        is_owner = list_info.get("my_role", "owner") == "owner"
        title_icon = "🛒" if is_owner else "👥"
        st.title(f"{title_icon} {list_name}")

        # --- Del liste (kun eier) ---
        if is_owner:
            with st.expander("👥 Del liste"):
                share_token = db.get_or_create_share_token(active_id)
                _base = (
                    os.environ.get("SHARE_BASE_URL", "").rstrip("/")
                    or "http://localhost:8501"
                )
                join_url = f"{_base}?join={share_token}"
                st.caption("Send denne lenken til den du vil dele listen med:")
                st.code(join_url, language=None)
                st.caption("Alle med lenken som har logget inn kan bli med.")

                st.divider()
                st.markdown("**Legg til via e-post:**")
                inv_email = st.text_input("E-post", placeholder="navn@eksempel.no", key=f"inv_email_{active_id}")
                if st.button("Legg til", key=f"inv_add_{active_id}", type="primary"):
                    found = db.get_user_by_email(inv_email.strip())
                    if not found:
                        st.warning("Ingen bruker funnet med den e-posten. Personen må ha logget inn minst én gang.")
                    elif found["id"] == _user_db_id:
                        st.info("Det er deg selv.")
                    else:
                        db.add_list_member(active_id, found["id"])
                        st.success(f"✓ {found['name'] or found['email']} lagt til")
                        st.rerun()

                members = db.get_list_members(active_id)
                if members:
                    st.divider()
                    st.markdown("**Nåværende members:**")
                    for m in members:
                        mc1, mc2 = st.columns([5, 1])
                        mc1.markdown(f"{m['name'] or m['email']} _{m['role']}_")
                        if mc2.button("✕", key=f"rm_member_{active_id}_{m['user_id']}", help="Fjern"):
                            db.remove_list_member(active_id, m["user_id"])
                            st.rerun()

        # Vis prissammenligning hvis tilgjengelig
        if st.session_state.liste_resultater is not None:
            if st.button("← Tilbake til varer"):
                st.session_state.liste_resultater = None
                st.rerun()
            _show_liste_resultater()
            return

        items = db.get_shopping_list_items(active_id)

        if items:
            if st.button(
                "🔍 Søk priser for alle varer", type="primary", use_container_width=True
            ):
                _search_list_prices(items)
                st.rerun()

        if not items:
            st.info(
                "Listen er tom. Legg til varer nedenfor, "
                "eller søk etter produkter og velg denne listen."
            )
        else:
            for item in items:
                c1, c2, c3 = st.columns([7, 1, 1])
                qty_str = f" × {item['quantity']}" if item.get("quantity", 1) > 1 else ""
                note_str = f"  _{item['note']}_" if item.get("note") else ""
                name_cap = item["original_name"].capitalize()
                if item["checked"]:
                    c1.markdown(f"~~{name_cap}{qty_str}{note_str}~~")
                else:
                    c1.markdown(f"{name_cap}{qty_str}{note_str}")
                chk_lbl = "☑" if item["checked"] else "☐"
                if c2.button(chk_lbl, key=f"chk_{item['id']}", use_container_width=True):
                    db.toggle_item_checked(item["id"])
                    st.rerun()
                if c3.button("✕", key=f"rmv_{item['id']}", use_container_width=True):
                    db.remove_shopping_list_item(item["id"])
                    st.rerun()

        # Legg til vare
        st.divider()
        st.subheader("Legg til vare")
        with st.form(f"add_form_{active_id}", clear_on_submit=True):
            ac1, ac2, ac3 = st.columns([5, 1, 2])
            new_name = ac1.text_input("Varenavn", placeholder="f.eks. havregryn")
            new_qty = ac2.number_input("Antall", min_value=1, value=1)
            new_note = ac3.text_input("Merknad", placeholder="f.eks. 1,5% fett")
            if st.form_submit_button("Legg til", type="primary") and new_name.strip():
                db.add_to_shopping_list(
                    active_id, new_name.strip(), quantity=int(new_qty), note=new_note or None
                )
                st.rerun()

        # Importer produkter
        with st.expander("📥 Importer produkter"):
            st.caption(
                "Lim inn en liste med produktnavn — ett per linje, "
                "eller skilt med komma / semikolon."
            )
            with st.form(f"import_form_{active_id}", clear_on_submit=True):
                import_dest = st.radio(
                    "Legg til i",
                    ["Aktiv liste", "Ny liste"],
                    horizontal=True,
                    key=f"import_dest_{active_id}",
                )
                new_list_name = st.text_input(
                    "Navn på ny liste",
                    placeholder="f.eks. Ukeshandel",
                    disabled=(import_dest == "Aktiv liste"),
                )
                raw_input = st.text_area(
                    "Produkter",
                    placeholder="melk\nbrød\negg, smør\nhavremel; appelsinjuice",
                    height=150,
                )
                if st.form_submit_button("Importer", type="primary"):
                    lines = raw_input.replace(";", "\n").replace(",", "\n").splitlines()
                    names = [n.strip() for n in lines if n.strip()]
                    if not names:
                        st.warning("Ingen produkter å importere.")
                    elif import_dest == "Ny liste":
                        target_name = new_list_name.strip() or "Importert liste"
                        new_id = db.create_shopping_list(_user_db_id, target_name)
                        for n in names:
                            db.add_to_shopping_list(new_id, n)
                        st.success(f"✓ Opprettet «{target_name}» med {len(names)} varer.")
                        st.session_state.active_list_id = new_id
                        st.rerun()
                    else:
                        for n in names:
                            db.add_to_shopping_list(active_id, n)
                        st.success(f"✓ La til {len(names)} varer i listen.")
                        st.rerun()

    st.divider()
    _prishistorikk_expander("hl_")


# ---------------------------------------------------------------------------
# Seksjon: Prishistorikk
# ---------------------------------------------------------------------------

def _prishistorikk_content(key_prefix: str = "") -> None:
    products = db.get_products_with_history()
    if not products:
        st.info(
            "Ingen prishistorikk ennå. "
            "Bruk **Søk priser for alle varer** i Handlelister for å samle prisdata."
        )
        return

    c1, c2 = st.columns([4, 2])
    with c1:
        selected = st.selectbox("Velg produkt", products, key=f"{key_prefix}ph_product")
    with c2:
        days = st.slider("Dager tilbake", 7, 365, 30, key=f"{key_prefix}ph_days")

    if not selected:
        return

    history = db.get_price_history(selected, days=days)
    if not history:
        st.info(f"Ingen data for **{selected}** de siste {days} dagene.")
        return

    df = pd.DataFrame(history)
    df["recorded_at"] = pd.to_datetime(df["recorded_at"]).dt.floor("D")

    stores_in_data = sorted(df["store"].unique())

    df_pivot = (
        df.pivot_table(index="recorded_at", columns="store", values="price", aggfunc="mean")
        .sort_index()
    )
    st.subheader(f"{selected.capitalize()}")
    st.line_chart(df_pivot, height=300)

    stat_cols = st.columns(len(stores_in_data))
    for col, store in zip(stat_cols, stores_in_data):
        sdf = df[df["store"] == store].sort_values("recorded_at")
        latest_price = sdf.iloc[-1]["price"]
        min_p = sdf["price"].min()
        max_p = sdf["price"].max()
        delta = latest_price - sdf.iloc[-2]["price"] if len(sdf) >= 2 else None
        col.metric(
            store,
            f"kr {latest_price:.2f}",
            delta=f"{delta:+.2f} kr" if delta is not None else None,
            delta_color="inverse",
            help=f"Min: {min_p:.2f} kr  /  Maks: {max_p:.2f} kr  /  {len(sdf)} målinger",
        )

    with st.expander("Vis rådata"):
        df_show = df[["recorded_at", "store", "price", "unit_price"]].copy()
        df_show.columns = ["Tidspunkt", "Butikk", "Pris (kr)", "Per enhet"]
        df_show = df_show.sort_values("Tidspunkt", ascending=False).reset_index(drop=True)
        st.dataframe(
            df_show,
            column_config={"Pris (kr)": st.column_config.NumberColumn(format="%.2f kr")},
            use_container_width=True,
            hide_index=True,
        )


def _show_prishistorikk() -> None:
    st.title("📈 Prishistorikk")
    _prishistorikk_content()


def _prishistorikk_expander(key_prefix: str) -> None:
    with st.expander("📈 Prishistorikk"):
        _prishistorikk_content(key_prefix=key_prefix)


# ---------------------------------------------------------------------------
# Seksjon: Normalisering
# ---------------------------------------------------------------------------

def _show_normalisering() -> None:
    st.title("🏷️ Normalisering")
    st.caption(
        "Sett ditt eget visningsnavn på produkter. "
        "**Ditt navn** overstyrer auto-normalisert navn overalt i appen. "
        "Tomt felt = bruk auto-normalisert."
    )

    nc1, nc2 = st.columns([4, 2])
    filter_text = nc1.text_input("Filtrer", placeholder="søk på produktnavn...", key="norm_filter")
    show_only_custom = nc2.toggle("Vis kun tilpassede", key="norm_only_custom")

    rows = db.list_normals_with_custom(_user_db_id, filter=filter_text or None)
    if not rows:
        st.info("Ingen produktnavn ennå. Søk etter produkter for å bygge opp listen.")
        return

    if show_only_custom:
        rows = [r for r in rows if r.get("custom_name")]

    st.caption(f"{len(rows)} produktnavn")

    # Bulk-handlinger
    ba1, ba2, _ = st.columns([2, 2, 3])
    if ba1.button("💾 Lagre alle endringer", type="primary"):
        saved = 0
        for row in rows:
            key = f"norm_edit_{row['id']}"
            current_db = row.get("custom_name") or ""
            new_val = st.session_state.get(key, current_db)
            if new_val != current_db:
                db.set_custom_name_by_id(int(row["id"]), new_val, _user_db_id)
                saved += 1
        if saved:
            st.success(f"✓ {saved} navn lagret")
            st.rerun()
        else:
            st.info("Ingen endringer å lagre")

    if ba2.button("🗑️ Fjern alle tilpassede"):
        for row in rows:
            if row.get("custom_name"):
                db.set_custom_name_by_id(int(row["id"]), "", _user_db_id)
        st.rerun()

    st.divider()

    # on_click-callback: settes FØR widget rendres → ingen konflikt
    def _set_norm(key: str, value: str) -> None:
        st.session_state[key] = value

    # Kolonneoverskrifter
    h1, h2, h3, h4, h5 = st.columns([3, 3, 3, 1, 1])
    h1.caption("**Original**")
    h2.caption("**Auto-normalisert**")
    h3.caption("**Ditt navn**")

    for row in rows:
        rid = row["id"]
        orig = row["original_name"]
        auto = row.get("auto_name") or ""
        current_custom = row.get("custom_name") or ""
        key = f"norm_edit_{rid}"

        # Pre-fill fra DB første gang (før widget rendres, ingen konflikt)
        if key not in st.session_state:
            st.session_state[key] = current_custom

        c1, c2, c3, c4, c5 = st.columns([3, 3, 3, 1, 1])
        c1.markdown(f"`{orig}`")
        c2.markdown(f"_{auto}_" if auto else "—")
        with c3:
            st.text_input(
                "", key=key, label_visibility="collapsed",
                placeholder="Ditt navn (tomt = bruk auto)"
            )
        with c4:
            st.button(
                "→", key=f"copy_orig_{rid}",
                on_click=_set_norm, args=(key, orig),
                help="Kopier original til 'Ditt navn'",
            )
        with c5:
            if auto:
                st.button(
                    "⟳", key=f"use_auto_{rid}",
                    on_click=_set_norm, args=(key, auto),
                    help="Bruk auto-normalisert",
                )


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    c_pic, c_info = st.columns([1, 3])
    with c_pic:
        if _user.get("picture"):
            st.image(_user["picture"], width=40)
    with c_info:
        st.write(f"**{_user['name']}**")
        st.caption(f"`{_user['email']}`")

    btn_cols = st.columns([1, 1])
    if btn_cols[0].button("Logg ut", use_container_width=True):
        auth.logout()
        st.rerun()
    if _is_admin:
        lbl = "Skjul 🔧" if st.session_state.show_admin else "🔧 Admin"
        if btn_cols[1].button(lbl, use_container_width=True, type="secondary"):
            st.session_state.show_admin = not st.session_state.show_admin
            st.rerun()

    st.divider()

    if kassal_configured():
        _vis_fysiske = db.get_user_setting(_user_db_id, "vis_fysiske_butikker", "0") == "1"
        _ny_verdi = st.toggle(
            "Vis fysiske butikker",
            value=_vis_fysiske,
            help="Inkluder priser fra Rema, Kiwi, Coop m.fl. via Kassal.app (kun prisreferanse — ikke netthandel)",
            key="toggle_fysiske",
        )
        if _ny_verdi != _vis_fysiske:
            db.set_user_setting(_user_db_id, "vis_fysiske_butikker", "1" if _ny_verdi else "0")
            st.session_state.kassal_results = {}
            st.rerun()

        # --- Nærmeste butikker ---
        _saved_pnr = db.get_user_setting(_user_db_id, "postnummer", "")
        _pnr_input = st.text_input(
            "📍 Ditt postnummer",
            value=_saved_pnr,
            max_chars=4,
            placeholder="f.eks. 0179",
            key="pnr_input",
            help="Brukes til å vise nærmeste fysiske butikker",
        )
        if _pnr_input.strip() != _saved_pnr:
            db.set_user_setting(_user_db_id, "postnummer", _pnr_input.strip())
            st.session_state.kassal_stores_cache = None
            st.rerun()

        if _pnr_input.strip():
            with st.expander("📍 Nærmeste butikker"):
                if st.session_state.kassal_stores_cache is None:
                    with st.spinner("Henter butikker..."):
                        st.session_state.kassal_stores_cache = fetch_physical_stores()
                all_phys = st.session_state.kassal_stores_cache or []
                coords = postnummer_to_coords(_pnr_input.strip())
                if coords and all_phys:
                    near = nearest_stores(coords[0], coords[1], all_phys, limit=8)
                    for s in near:
                        st.caption(
                            f"**{s['name']}**  \n"
                            f"{s.get('address', '')}  \n"
                            f"📏 {s['_dist_km']} km"
                        )
                elif not coords:
                    st.warning("Fant ikke postnummeret — sjekk at det er 4 siffer.")
                else:
                    st.info("Ingen butikker funnet.")
        st.divider()

    _wl_triggered = sum(1 for w in db.get_watchlist(_user_db_id) if w["status"] == "triggered")
    _nav_items = [
        ("🔍 Søk", "søk"),
        ("🛒 Handlelister", "handlelister"),
        (f"⭐ Varslingsliste{f' ({_wl_triggered})' if _wl_triggered else ''}", "varslingsliste"),
        ("🏷️ Normalisering", "normalisering"),
    ]
    for _label, _key in _nav_items:
        _active = st.session_state.section == _key
        if st.button(
            _label,
            use_container_width=True,
            type="primary" if _active else "secondary",
            key=f"nav_{_key}",
        ):
            st.session_state.section = _key
            st.rerun()


# ---------------------------------------------------------------------------
# Hovedinnhold
# ---------------------------------------------------------------------------

if st.session_state.join_feedback:
    level, msg = st.session_state.join_feedback
    getattr(st, level)(msg)
    st.session_state.join_feedback = None

if st.session_state.show_admin and _is_admin:
    _admin_panel()
    st.stop()

if st.session_state.section == "søk":
    _show_search()
elif st.session_state.section == "handlelister":
    _show_handlelister()
elif st.session_state.section == "varslingsliste":
    _show_varslingsliste()
elif st.session_state.section == "normalisering":
    _show_normalisering()
