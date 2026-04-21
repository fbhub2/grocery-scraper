import json
import streamlit as st
import pandas as pd
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, str(Path(__file__).parent))
from scrapers import oda_search, meny_search

st.set_page_config(page_title="Prissammenligning", page_icon="🛒", layout="wide")

STORES = {"Oda": oda_search, "Meny": meny_search}
LISTE_FILE = Path(__file__).parent / "handleliste.json"


def load_liste() -> list[str]:
    if LISTE_FILE.exists():
        try:
            return json.loads(LISTE_FILE.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


def save_liste(liste: list[str]) -> None:
    LISTE_FILE.write_text(
        json.dumps(liste, ensure_ascii=False, indent=2), encoding="utf-8"
    )


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
        for vare in list(st.session_state.handleliste):
            c1, c2 = st.columns([5, 1])
            c1.write(vare.capitalize())
            if c2.button("✕", key=f"fjern_{vare}", help=f"Fjern {vare}"):
                st.session_state.handleliste.remove(vare)
                save_liste(st.session_state.handleliste)
                st.rerun()

        st.divider()

        if st.button("🔍 Søk alle på listen", type="primary", use_container_width=True):
            varer = list(st.session_state.handleliste)
            rows = []
            totals = {s: 0.0 for s in STORES}
            mangler: dict[str, list[str]] = {s: [] for s in STORES}

            with st.spinner("Søker alle varer på listen ..."):
                for vare in varer:
                    res, _ = run_search(vare, 1)
                    row: dict = {"Vare": vare.capitalize()}
                    for store_name in STORES:
                        prods = res.get(store_name, [])
                        if prods:
                            row[store_name] = prods[0].price
                            totals[store_name] += prods[0].price
                        else:
                            row[store_name] = None
                            mangler[store_name].append(vare)
                    rows.append(row)

            st.session_state.liste_resultater = {
                "rows": rows,
                "totals": totals,
                "mangler": mangler,
            }
            st.session_state.search_results = None
            st.rerun()


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

    st.session_state.search_results = {
        k: [p.to_dict() for p in v] for k, v in results.items()
    }
    st.session_state.search_errors = errors
    st.session_state.last_query = query.strip()
    st.session_state.liste_resultater = None


# --- Søkeresultater ---
if st.session_state.search_results is not None:
    q = st.session_state.last_query
    results = st.session_state.search_results
    errors = st.session_state.search_errors

    liste_set = {v.lower() for v in st.session_state.handleliste}

    cols = st.columns(len(STORES))
    for col, store in zip(cols, STORES):
        with col:
            st.subheader(store)
            if store in errors:
                st.error(f"Feil: {errors[store]}")
            elif not results.get(store):
                st.info("Ingen resultater")
            else:
                for i, p in enumerate(results[store]):
                    price_line = f"kr {p['price']:.2f}"
                    if p.get("unit_price"):
                        price_line += f"  _{p['unit_price']}_"
                    st.markdown(f"**{p['name']}**  \n{price_line}")
                    if p.get("url"):
                        st.markdown(f"[Se produkt]({p['url']})")
                    if p["name"].lower() in liste_set:
                        st.caption("✓ På handlelisten")
                    else:
                        if st.button("➕ Legg til liste", key=f"legg_{store}_{i}"):
                            st.session_state.handleliste.append(p["name"])
                            save_liste(st.session_state.handleliste)
                            st.rerun()
                    st.divider()

    all_rows = [
        {
            "Butikk": store,
            "Produkt": p["name"],
            "Pris (kr)": p["price"],
            "Per enhet": p.get("unit_price") or "",
        }
        for store, prods in results.items()
        for p in prods
    ]
    if all_rows:
        st.subheader("Alle resultater sortert på pris")
        df = pd.DataFrame(all_rows).sort_values("Pris (kr)").reset_index(drop=True)
        st.dataframe(
            df,
            column_config={
                "Pris (kr)": st.column_config.NumberColumn(format="%.2f kr")
            },
            use_container_width=True,
            hide_index=True,
        )


# --- Handlelistesøk-resultater ---
elif st.session_state.liste_resultater is not None:
    lr = st.session_state.liste_resultater
    rows = lr["rows"]
    totals: dict[str, float] = lr["totals"]
    mangler: dict[str, list[str]] = lr["mangler"]

    st.subheader("Handlelisteprissammenligning")

    # Per-item: finn billigste butikk og beregn summer
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

    col_config = {s: st.column_config.NumberColumn(s, format="%.2f kr") for s in STORES}
    st.dataframe(
        pd.DataFrame(rows_display),
        column_config=col_config,
        use_container_width=True,
        hide_index=True,
    )

    # Oppsummering
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
