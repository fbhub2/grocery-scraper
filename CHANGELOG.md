# CHANGELOG

## [Unreleased — v2.0 pågående]

Spec: GROCERY_SCRAPER_SPEC.md (2026-05-01)

### feature/normalization (mai 2026)
- `auto_normalize()`: lowercase, CamelCase-split, COMPOUND_SPLITS (8 norske sammensetninger), volum-norm (1000g→1kg, "liter"→"l")
- `resolve_name()`: eneste UI-funksjon for produktnavn — prioritet custom > auto > original
- `check_threshold()`: absolutt/relativ/sale terskellogikk
- `tasks.py`: `run_auto_normalize()` (hopper over eksisterende auto_name), CLI-kjøring
- 97 tester grønne

### feature/db-foundation (mai 2026)
- Alle v2.0-tabeller: store, product, normal, user_normal, user, price_fetch,
  product_price_history, shopping_list, shopping_list_item, watchlist, search_history
- 30+ nye db-funksjoner (v1.x beholdes for backward compat)
- 37 nye tester — 71 totalt

---

## [v1.x — levert]

### feature/prisvarsel (PR #3 · apr 2026)
- `st.success()` banner per vare med prisfall etter «Søk alle på listen»
- Badge per vare i sidebar
- `get_price_trend()` bugfix: `ORDER BY id DESC` (ikke recorded_at — ikke-deterministisk ved like timestamps)

### feature/prishistorikk (PR #2 · apr 2026)
- `price_history`-tabell i SQLite
- `record_price()`, `get_price_trend()`
- Trend-kolonne (↑↓→) per butikk i handlelistetabell

### feature/produktbilde (PR #1 · apr 2026)
- `image_url` fra Oda (`thumbnail.url`) og Meny (`bilder.ngdata.no`)
- Vises i søkeresultater og sidebar

### feature/mcp-server → grocery_scraper_mcp.py (apr 2026)
- `search_products`, `compare_prices`, `get_store_list`
- `add_to_list`, `add_multiple_to_list`, `get_list`, `import_obs_catalog`
- `rapidfuzz>=3.0` for fuzzy-ranking
- Omdøpt fra `mcp_server.py` for unik navngiving
- Fix: fjernet `print()` til stdout som forstyrret MCP stdio-protokollen
- Fix: `sys.path.insert()` for Electron-prosess-spawning

### feature/obs-import (apr 2026)
- OBS tilbudsavis-import via Claude Vision + MCP-tool
- `obs_products`-tabell i SQLite med gyldighetsperiode
- Vises i søkeresultater og sidebar med OBS-badge

### feature/ui-sokresultater-v2 (apr 2026)
- Søkeresultater i `st.dataframe` med radseleksjon
- Butikk-multiselect, sorteringsvalg
- "Legg til valgte (N) på handlelisten"
- `_best_product()` for volume-matching
- Enhetspris per butikk i handlelistetabell

### feature/db-search-term (apr 2026)
- `list_items`-tabell: `search_term`, `volume`, `brand`-kolonner
- `remove_item(item_id=)` for presis sletting
- Auto-migrering via `PRAGMA table_info()`

### Grunnstruktur (apr 2026)
- Oda + Meny scraper via httpx
- `Product`-dataclass med `split_name_variant()`
- SQLite handleliste
- Streamlit web-app (`app.py`)
- CLI (`main.py`)
