import streamlit as st
import pandas as pd
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, str(Path(__file__).parent))
from scrapers import oda_search, meny_search

STORES = {"Oda": oda_search, "Meny": meny_search}

st.set_page_config(page_title="Prissammenligning", page_icon="🛒", layout="wide")
st.title("🛒 Prissammenligning")
st.caption("Sammenligner priser fra Oda og Meny i sanntid")

with st.form("search_form"):
    col1, col2, col3 = st.columns([5, 1, 1])
    with col1:
        query = st.text_input("Søk etter produkt", placeholder="f.eks. havregryn, smør, egg...")
    with col2:
        limit = st.number_input("Antall", min_value=1, max_value=20, value=5)
    with col3:
        st.write("")
        submitted = st.form_submit_button("Søk", type="primary", use_container_width=True)

if submitted:
    if not query.strip():
        st.warning("Skriv inn et søkeord.")
        st.stop()

    results: dict = {}
    errors: dict = {}

    with st.spinner(f'Søker etter "{query.strip()}" ...'):
        with ThreadPoolExecutor(max_workers=len(STORES)) as executor:
            futures = {
                executor.submit(fn, query.strip(), limit): name
                for name, fn in STORES.items()
            }
            for future in as_completed(futures):
                name = futures[future]
                try:
                    results[name] = [p.to_dict() for p in future.result()]
                except Exception as e:
                    errors[name] = str(e)
                    results[name] = []

    cols = st.columns(len(STORES))
    for col, store in zip(cols, STORES):
        with col:
            st.subheader(store)
            if store in errors:
                st.error(f"Feil: {errors[store]}")
            elif not results.get(store):
                st.info("Ingen resultater")
            else:
                for p in results[store]:
                    price_line = f"kr {p['price']:.2f}"
                    if p.get("unit_price"):
                        price_line += f"  _{p['unit_price']}_"
                    st.markdown(f"**{p['name']}**  \n{price_line}")
                    if p.get("url"):
                        st.markdown(f"[Se produkt]({p['url']})")
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
            column_config={"Pris (kr)": st.column_config.NumberColumn(format="%.2f kr")},
            use_container_width=True,
            hide_index=True,
        )
