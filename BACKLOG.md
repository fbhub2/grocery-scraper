# Backlog – grocery-scraper / Prissammenligning

Prioritert liste. Øverst = viktigst. Flytt fritt mellom seksjoner.

---

## 🔴 Høy prioritet (neste sprint)

*(ingen gjenstående)*

---

## 🟡 Medium prioritet

*(ingen gjenstående)*

---

## 🔵 Lav prioritet / langsiktig

- [ ] Rema 1000 støtte – når/hvis API blir tilgjengelig igjen

---

## ✅ Ferdig

- [x] **Grunnstruktur** — `first commit` · apr 2026
  - Oda + Meny scraper via httpx, CLI (`main.py`), Streamlit (`app.py`)
  - `Product`-dataclass med `split_name_variant()`

- [x] **Handleliste + UI-forbedringer** — `feature/handleliste` · apr 2026
  - SQLite handleliste, legg til/fjern varer, per-butikk kolonner i UI

- [x] **SQLite-lagring** (`db.py`) — `feature/db-search-term` · apr 2026
  - Tabeller: `shopping_lists`, `list_items` (med `search_term`, `volume`), `obs_products`
  - `remove_item(item_id=)` for presis sletting, auto-migrering

- [x] **Produktnavn-normalisering** (`normalize.py`) — `feature/db-search-term` · apr 2026
  - `normalize_search_term()` – strippar volum-tokens for kryssbutikk-matching
  - `parse_product_name()` – strukturert ekstraksjon (brand, volum, enhet)

- [x] **OBS tilbudsavis-import** — `feature/obs-import` · apr 2026
  - Claude Vision parser PDF/bilde → `import_obs_catalog` MCP-tool lagrer i SQLite
  - Vises i søkeresultater og sidebar med gyldighetsperiode

- [x] **MCP-server grunnstruktur** (`mcp_server.py`) — `feature/mcp-server` · apr 2026
  - `search_products`, `compare_prices`, `get_store_list`
  - `add_to_list`, `add_multiple_to_list`, `get_list`, `import_obs_catalog`
  - `rapidfuzz>=3.0` for fuzzy-ranking

- [x] **Søkeresultater-tabell øverst med filtre** — `feature/ui-sokresultater-v2` · apr 2026
  - Butikk-multiselect, sorteringsvalg
  - Radseleksjon → "Legg til valgte (N) på handlelisten"

- [x] **Volume-matching i handlelistesøk** — `feature/ui-sokresultater-v2` · apr 2026
  - `_best_product()` velger beste volum-match
  - Enhetspris per butikk i handlelistetabell

- [x] **Fix: prosent i produktnavn** (`split_name_variant`) — `fix/split-name-variant-percent` · apr 2026
  - `0,5%` beholdes i produktnavn, flyttes ikke til variant-kolonne

- [x] **Produktbilde i resultat** — PR #1 · `feature/produktbilde` · apr 2026
  - `image_url` fra Oda (`thumbnail.url`) og Meny (`bilder.ngdata.no`) vises i søk og sidebar

- [x] **Prishistorikk over tid** — PR #2 · `feature/prishistorikk` · apr 2026
  - `price_history`-tabell i SQLite, `record_price()`, `get_price_trend()`
  - Trend-kolonne (↑↓→) per butikk i handlelistetabell

- [x] **Varsling ved prisfall** — PR #3 · `feature/prisvarsel` · apr 2026
  - `st.success()` banner per vare med prisfall etter «Søk alle på listen»
  - Badge per vare i sidebar når prisfall er registrert

---

## 🪦 Parkert / ikke aktuelt nå

- ~~Kassal API-integrasjon~~ — vurdert, ikke i bruk; Oda/Meny scrapes direkte
- ~~Supabase sky-lagring~~ — overkill, SQLite foretrekkes
- ~~Rema 1000 aktivering~~ — `rema.py` finnes men API er ikke-funksjonelt

---

## 🐛 Kjente bugs

- [ ] **MCP grocery-scraper laster ikke i Claude Desktop** — mai 2026
  - Serveren fungerer 100% isolert (full JSON-RPC handshake OK, alle 7 tools returneres)
  - `homeassistant` MCP (identisk mønster, `"command": "python"`, C:\ClaudeMCP\) laster fint
  - Forsøkt: sys.path-fix, full Python-sti, cwd, filnavn-rename, kopi til C:\ClaudeMCP\, rekkefølge i config
  - Mistanke: Desktop Commander sin `allowedDirectories`/konflikthåndtering, eller Electron sandbox-problem spesifikt for dette prosjektet
  - Neste: sjekk om Electron-prosessen for grocery-scraper faktisk startes (Task Manager), og om det finnes feillogg i `%LOCALAPPDATA%\Claude\`
