# Backlog – grocery-scraper / Prissammenligning

Prioritert liste. Øverst = viktigst. Flytt fritt mellom seksjoner.

---

## 🔴 Høy prioritet (neste sprint)

*(ingen gjenstående)*

---

## 🟡 Medium prioritet

- [ ] **Produktbilde i resultat**
  - `image_url` er tilgjengelig i API-svar fra Oda og Meny
  - Vis i Streamlit med `st.image()` ved søk og i handleliste

---

## 🔵 Lav prioritet / langsiktig

- [ ] Prishistorikk over tid – spore prisutvikling per produkt i SQLite
- [ ] Varsling ved prisfall på favoritter
- [ ] Rema 1000 støtte – når/hvis API blir tilgjengelig igjen

---

## ✅ Ferdig

- [x] **MCP-server grunnstruktur** (`mcp_server.py`)
  - `search_products`, `compare_prices`, `get_store_list`
  - `add_to_list`, `add_multiple_to_list`, `get_list`, `import_obs_catalog`
- [x] **SQLite-lagring** (`db.py`)
  - Tabeller: `shopping_lists`, `list_items` (med `search_term`, `volume`), `obs_products`
  - `remove_item(item_id=)` for presis sletting
  - Auto-migrering for eksisterende databaser
- [x] **Produktnavn-normalisering** (`normalize.py`)
  - `normalize_search_term()` – strippar volum-tokens for kryssbutikk-matching
  - `parse_product_name()` – strukturert ekstraksjon (brand, volum, enhet)
- [x] **RapidFuzz fuzzy-søk**
  - `rapidfuzz>=3.0` i requirements.txt
  - Brukes i `mcp_server.py` for fuzzy-ranking av søkeresultater
- [x] **OBS tilbudsavis-import**
  - Claude Vision parser PDF/bilde → `import_obs_catalog` MCP-tool lagrer i SQLite
  - Vises i søkeresultater og sidebar med gyldighetsperiode
- [x] **Søkeresultater-tabell øverst med filtre**
  - Butikk-multiselect, sorteringsvalg
  - Radseleksjon → "Legg til valgte (N) på handlelisten"
- [x] **Volume-matching i handlelistesøk**
  - `_best_product()` velger beste volum-match
  - Enhetspris per butikk i handlelistetabell

---

## 🪦 Parkert / ikke aktuelt nå

- ~~Kassal API-integrasjon~~ — vurdert, ikke i bruk; Oda/Meny scrapes direkte
- ~~Supabase sky-lagring~~ — overkill, SQLite foretrekkes
- ~~Rema 1000 aktivering~~ — `rema.py` finnes men API er ikke-funksjonelt

---

## 🐛 Kjente bugs

*(ingen registrert)*
