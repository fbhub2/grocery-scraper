import streamlit as st
import pandas as pd
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, str(Path(__file__).parent))
from scrapers import oda_search, meny_search
from scrapers.base import split_name_variant
import db
from normalize import parse_product_name, normalize_search_term

st.set_page_config(page_title="Prissammenligning", page_icon="🛒", layout="wide")

STORES = {"Oda": oda_search, "Meny": meny_search}


def load_liste() -> list[dict]:
    return db.get_list("default")


def _item_display(name: str, volume: str | None) -> None:
    st.write(name.capitalize())
    if volume:
        st.caption(volume)


def _query_variants(query: str, volume: str | None) -> list[str]:
    variants = [query]
    if volume:
        v_nospace = volume.replace(" ", "")
        variants.append(f"{query} {v_nospace}")
    return list(dict.fromkeys(variants))


def _best_product(products: list, preferred_volume: str | None):
    """Returnerer produktet som best matcher preferred_volume, eller første resultat."""
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


def _best_price(products: list, preferred_volume: str | None) -> float | None:
    p = _best_product(products, preferred_volume)
    if p is None:
        return None
    return p["price"] if isinstance(p, dict) else p.price


def run_search(query: str, limit: int) -> tuple[dict, dict]:
    results, errors = {}, {}
    with ThreadPoolExecutor(max_workers=len(STORES)) as executor:
        futures = {
            executor.submit(fn, query, limit): name for name, fn in STORES.items()
        }
        for future in as_completed(futures):
            name = futures[future]
            try:
                results[name] = future.result()
            except Exception as e:
                errors[name] = str(e)
                results[name] = []

    obs_results = db.search_obs(query)
    results["OBS 📰"] = obs_results

    return results, errors


# --- Session state ---
if "handleliste" not in st.session_state:
    st.session_state.handleliste = load_liste()
if "search_results" not in st.session_state:
    st.session_state.search_results = None
if "search_errors" not in st.session_state:
    st.session_state.search_errors = {}
if "last_query" not in st.session_state:
    st.session_state.last_query = ""
if "liste_resultater" not in st.session_state:
    st.session_state.liste_resultater = None


# --- Sidebar: handleliste ---
with st.sidebar:
    st.header("🛒 Handleliste")

    if not st.session_state.handleliste:
        st.caption("Listen er tom. Søk etter en vare og legg den til.")
    else:
        handleliste_copy = list(st.session_state.handleliste)
        for idx, item in enumerate(handleliste_copy):
            c1, c2 = st.columns([5, 1])
            with c1:
                _item_display(item["product_name"], item.get("volume"))
            if c2.button("✕", key=f"fjern_idx_{idx}", help=f"Fjern {item['product_name']}"):
                db.remove_item("default", item["product_name"], item_id=item.get("id"))
                st.session_state.handleliste = [
                    i for i in st.session_state.handleliste if i.get("id") != item.get("id")
                ]
                st.rerun()

        st.divider()

        if st.button("🔍 Søk alle på listen", type="primary", use_container_width=True):
            varer = list(st.session_state.handleliste)
            rows = []
            totals = {s: 0.0 for s in STORES}
            mangler: dict[str, list[str]] = {s: [] for s in STORES}

            with st.spinner("Søker alle varer på listen ..."):
                for item in varer:
                    vare = item["product_name"]
                    preferred_volume = item.get("volume")
                    search_query = item.get("search_term") or normalize_search_term(vare)
                    res, _ = run_search(search_query, 3)
                    vare_label = vare.capitalize()
                    if preferred_volume:
                        vare_label += f" ({preferred_volume})"
                    row: dict = {"Vare": vare_label}
                    for store_name in STORES:
                        prods = res.get(store_name, [])
                        best = _best_product(prods, preferred_volume)
                        if best:
                            price = best.price if hasattr(best, "price") else best["price"]
                            unit_price = getattr(best, "unit_price", None) or (
                                best.get("unit_price") if isinstance(best, dict) else None
                            )
                            row[store_name] = price
                            row[f"{store_name} (enhet)"] = unit_price or ""
                            totals[store_name] += price
                        else:
                            row[store_name] = None
                            row[f"{store_name} (enhet)"] = ""
                            mangler[store_name].append(vare)
                    rows.append(row)

            st.session_state.liste_resultater = {
                "rows": rows,
                "totals": totals,
                "mangler": mangler,
            }
            st.session_state.search_results = None
            st.rerun()

    # --- OBS-status ---
    st.divider()
    st.subheader("📰 OBS-tilbudsavis")
    obs_status = db.get_obs_status()

    if obs_status["has_data"]:
        if obs_status["is_expired"]:
            st.warning("⏰ OBS-priser utløpt")
        else:
            st.success(f"✅ Gyldig til {obs_status['valid_to']}")

        col1, col2 = st.columns(2)
        col1.metric("Produkter", obs_status["total_products"])
        col2.write(f"**Uke:** {obs_status['valid_week']}")

        if st.button("🔄 Oppdater OBS", use_container_width=True, key="update_obs"):
            st.info("""
                **Slik importerer du ny OBS-uke:**

                1. Åpne https://kundeavis-obs.coop.no/fso/
                2. Last ned eller ta screenshot av kundeavisen
                3. Åpne Claude Desktop eller claude.ai/code
                4. Bruk `import_obs_catalog` tool med PDF/bilde
                5. Produktene lagres automatisk i databasen

                **Eller:** Les detaljert guide i `obs_import.md`
            """)
    else:
        st.caption("Ingen OBS-data importert ennå")
        st.button("📥 Importer OBS nå", use_container_width=True, key="import_obs_first")


# --- Topp ---
st.title("🛒 Prissammenligning")
st.caption("Sammenligner priser fra Oda og Meny i sanntid")

with st.form("search_form"):
    col1, col2, col3 = st.columns([5, 1, 1])
    with col1:
        query = st.text_input(
            "Søk etter produkt", placeholder="f.eks. havregryn, smør, egg..."
        )
    with col2:
        limit = st.number_input("Antall", min_value=1, max_value=20, value=5)
    with col3:
        st.write("")
        submitted = st.form_submit_button("Søk", type="primary", use_container_width=True)

if submitted:
    if not query.strip():
        st.warning("Skriv inn et søkeord.")
        st.stop()

    with st.spinner(f'Søker etter "{query.strip()}" ...'):
        results, errors = run_search(query.strip(), int(limit))

    converted_results = {}
    for store, products in results.items():
        if store == "OBS 📰":
            converted_results[store] = products
        else:
            converted_results[store] = [p.to_dict() if hasattr(p, "to_dict") else p for p in products]

    st.session_state.search_results = converted_results
    st.session_state.search_errors = errors
    st.session_state.last_query = query.strip()
    st.session_state.liste_resultater = None


# --- Søkeresultater ---
if st.session_state.search_results is not None:
    q = st.session_state.last_query
    results = st.session_state.search_results
    errors = st.session_state.search_errors

    liste_set = {item["product_name"].lower() for item in st.session_state.handleliste}

    # --- Sammenstilt tabell ØVERST med filtre ---
    all_rows = [
        {
            "Butikk": store,
            "Produkt": p.get("product_name") if store == "OBS 📰" else p.get("name"),
            "Mengde": p.get("volume") if store == "OBS 📰" else p.get("variant") or "",
            "Pris (kr)": p["price"],
            "Per enhet": p.get("unit_price") or "",
        }
        for store, prods in results.items()
        for p in prods
    ]

    if all_rows:
        st.subheader(f'Resultater for "{q}"')

        f1, f2 = st.columns([3, 2])
        with f1:
            available_stores = list(results.keys())
            valgte_butikker = st.multiselect(
                "Vis butikker", available_stores, default=available_stores,
                key="filter_butikker",
            )
        with f2:
            sorter_etter = st.selectbox(
                "Sorter etter", ["Pris (kr)", "Produkt", "Butikk"],
                key="filter_sortering",
            )

        df = pd.DataFrame(all_rows)
        if valgte_butikker:
            df = df[df["Butikk"].isin(valgte_butikker)]
        df = df.sort_values(sorter_etter, na_position="last").reset_index(drop=True)

        selection = st.dataframe(
            df,
            column_config={
                "Pris (kr)": st.column_config.NumberColumn(format="%.2f kr"),
            },
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="multi-row",
        )

        selected_rows = selection.selection.rows if selection else []
        if selected_rows:
            if st.button(f"➕ Legg til valgte ({len(selected_rows)}) på handlelisten"):
                for row_idx in selected_rows:
                    row = df.iloc[row_idx]
                    name = row["Produkt"]
                    if name and name.lower() not in liste_set:
                        db.add_item(
                            "default", name,
                            store=row["Butikk"],
                            price=float(row["Pris (kr)"]),
                            volume=row["Mengde"] or None,
                            search_term=normalize_search_term(name),
                        )
                st.session_state.handleliste = load_liste()
                st.rerun()

    st.divider()

    # --- Per-butikk kolonner ---
    stores_to_show = list(results.keys())
    cols = st.columns(len(stores_to_show))
    for col, store in zip(cols, stores_to_show):
        with col:
            st.subheader(store)
            if store in errors:
                st.error(f"Feil: {errors[store]}")
            elif not results.get(store):
                st.info("Ingen resultater")
            else:
                for i, p in enumerate(results[store]):
                    is_obs = store == "OBS 📰"

                    name = p.get("product_name") if is_obs else p.get("name")
                    price = p.get("price")
                    unit_price = p.get("unit_price") if not is_obs else None
                    variant = p.get("volume") if is_obs else p.get("variant")
                    url = p.get("url") if not is_obs else None
                    valid_to = p.get("valid_to") if is_obs else None

                    price_line = f"kr {price:.2f}"
                    if unit_price:
                        price_line += f"  _{unit_price}_"

                    st.markdown(f"**{name}**")
                    if variant:
                        st.caption(variant)
                    st.markdown(price_line)

                    if is_obs and valid_to:
                        from datetime import date
                        is_expired = valid_to < date.today().isoformat()
                        if is_expired:
                            st.caption("⏰ Utløpt")
                        else:
                            st.caption(f"✅ Gyldig til {valid_to}")

                    if url:
                        st.markdown(f"[Se produkt]({url})")

                    if name.lower() in liste_set:
                        st.caption("✓ På handlelisten")
                    else:
                        if st.button("➕ Legg til liste", key=f"legg_{store}_{i}"):
                            search_term = normalize_search_term(name)
                            db.add_item(
                                "default", name,
                                store=store, price=price,
                                volume=variant, search_term=search_term,
                            )
                            st.session_state.handleliste = load_liste()
                            st.rerun()
                    st.divider()


# --- Handlelistesøk-resultater ---
elif st.session_state.liste_resultater is not None:
    lr = st.session_state.liste_resultater
    rows = lr["rows"]
    totals: dict[str, float] = lr["totals"]
    mangler: dict[str, list[str]] = lr["mangler"]

    st.subheader("Handlelisteprissammenligning")

    optimal_total = 0.0
    store_best_sums = {s: 0.0 for s in STORES}
    rows_display = []
    for row in rows:
        prices = {s: row[s] for s in STORES if row.get(s) is not None}
        if prices:
            best = min(prices, key=prices.get)
            store_best_sums[best] += prices[best]
            optimal_total += prices[best]
        else:
            best = "—"
        rows_display.append({**row, "Billigst": best})

    col_config: dict = {}
    for s in STORES:
        col_config[s] = st.column_config.NumberColumn(s, format="%.2f kr")
        col_config[f"{s} (enhet)"] = st.column_config.TextColumn(f"{s}/enhet")

    st.dataframe(
        pd.DataFrame(rows_display),
        column_config=col_config,
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Oppsummering")
    m_cols = st.columns(1 + len(STORES))
    m_cols[0].metric("🏆 Optimal sum", f"kr {optimal_total:.2f}",
                     help="Kjøper billigste alternativ per vare på tvers av butikker")
    for i, store in enumerate(STORES, 1):
        delta = totals[store] - optimal_total
        m_cols[i].metric(
            f"{store}",
            f"kr {store_best_sums[store]:.2f}",
            delta=f"Alt på {store}: kr {totals[store]:.2f}  (+kr {delta:.2f})" if delta > 0.01 else f"Alt på {store}: kr {totals[store]:.2f}",
            delta_color="off",
            help=f"Sum av varer der {store} er billigst. Kjøper du alt på {store}: kr {totals[store]:.2f}",
        )

    for store, items in mangler.items():
        if items:
            st.warning(f"{store}: ingen treff for: {', '.join(items)}")
