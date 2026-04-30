# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

Norwegian grocery price comparison tool. Scrapes Oda and Meny via direct HTTP. OBS (Coop) data is imported from the weekly ad PDF/image via Claude vision and stored locally in SQLite — not scraped live. Two entry points: a CLI (`main.py`) and a Streamlit web app (`app.py`).

## Running the app

```bash
# Streamlit web UI
streamlit run app.py

# CLI
python main.py "melk" -n 5 -o resultater.json
```

Dependencies: `pip install -r requirements.txt`
Required: `httpx>=0.27`, `streamlit>=1.35`, `pandas>=2.0`, `mcp>=1.0`, `rapidfuzz>=3.0`

## Architecture

### Data flow
1. User search → `scrapers/<store>.py` fires HTTP GET to the store's undocumented JSON API
2. Raw API response parsed into `Product` dataclass (`scrapers/base.py`)
3. `split_name_variant()` strips size/volume tokens from product names; percentage tokens (0,5%, 3,5%) are **kept in the product name**, not moved to variant
4. OBS results come from `db.search_obs()` (local SQLite), not live HTTP
5. Results returned to caller (`app.py` or `main.py`)

### Scrapers (`scrapers/`)

Each scraper exposes `search(query, limit) -> list[Product]`, re-exported from `scrapers/__init__.py`.

| File | Store | API endpoint | Active in app.py |
|------|-------|-------------|-----------------|
| `oda.py` | Oda | `https://oda.com/api/v1/search/mixed/` | Yes |
| `meny.py` | Meny | `https://platform-rest-prod.ngdata.no/api/episearch/1300/autosuggest` | Yes |
| `rema.py` | Rema 1000 | `https://www.rema.no/api/products` | No (file exists, not integrated) |

### `scrapers/base.py`
- `Product` dataclass: `name`, `price`, `unit_price`, `url`, `variant`
- `split_name_variant(full)`: extracts size tokens (`1,75 l`, `540 g`) → `(clean_name, variant_string | None)`. Percentages (`0,5%`) stay in the name.

### `db.py` (SQLite — `grocery.db`)

Three tables:

**`shopping_lists`**: id, name, created_at

**`list_items`**: id, list_id, product_name, brand, volume, store, price, image_url, quantity, added_at, checked, search_term
- `search_term`: normalized query used when the item was added (used for smarter re-search)
- Auto-migration: adds `search_term` column to existing databases

**`obs_products`**: id, product_name, brand, volume, price, normal_price, valid_from, valid_to, source, image_url, valid_week, imported_at, valid_updated_at
- Auto-migration: adds `valid_week`, `valid_updated_at` to existing databases

Key functions:
- `add_item(list_name, product_name, ..., volume=, search_term=)` — saves volume and search_term
- `get_list(list_name) -> list[dict]` — returns full row dicts including `id`
- `remove_item(list_name, product_name, item_id=None)` — use `item_id` for precise deletion
- `search_obs(query)` — LIKE search on product_name, only non-expired rows
- `add_obs_products(products)` — batch insert for OBS import
- `get_obs_status()` — returns has_data, total_products, valid_from/to, valid_week, is_expired
- `clear_expired_obs()` — delete expired OBS rows, returns count

### `normalize.py`
- `normalize_search_term(raw)` — strips volume tokens, lowercase. `"Tine Lettmelk 1,5 l"` → `"tine lettmelk"`
- `parse_product_name(raw_name)` — returns `{raw, product_name, volume, brand, unit}`. Used by MCP `compare_prices`.

### `app.py` (Streamlit)

**Session state keys:**
- `handleliste`: `list[dict]` — full db rows from `get_list()`, **not** a list of strings
- `search_results`: `dict[store → list[dict]]` — current search results
- `search_errors`: `dict[store → str]`
- `last_query`: str
- `liste_resultater`: `dict` with keys `rows`, `totals`, `mangler`

**Helper functions:**
- `load_liste()` → `list[dict]` from `db.get_list("default")`
- `_item_display(name, volume)` — renders product name + volume as separate lines in sidebar
- `_query_variants(query, volume)` — generates search variants (with/without volume)
- `_best_product(products, preferred_volume)` — picks best volume match from results list; handles both `Product` objects and dicts
- `_best_price(products, preferred_volume)` → float or None

**Search results layout:**
1. Sammenstilt tabell **øverst** — filtre: butikk-multiselect + sorteringsvalg (pris/produkt/butikk)
2. Rad-seleksjon i tabell → "Legg til valgte (N) på handlelisten" (uses `on_select="rerun"`, requires streamlit>=1.35)
3. Per-butikk kolonner under tabellen

**Handlelistesøk ("Søk alle på listen"):**
- Uses `item["search_term"]` from db if available, else `normalize_search_term(vare)`
- Fetches 3 results per store and picks best volume match via `_best_product()`
- Table shows enhetspris (unit price) per store in separate columns (`{store} (enhet)`)

**"Legg til liste" saves:** `volume`, `search_term` (via `normalize_search_term`) in addition to name/store/price

**OBS in sidebar:** Shows valid_to date, product count, expired warning. Import instructions shown on button click.

**Shopping list persistence:** SQLite (`grocery.db`). No `handleliste.json`.

### `mcp_server.py` (MCP)

`.mcp.json` configures the local MCP server for Claude Code and Claude Desktop.

Available tools:
| Tool | Description |
|------|-------------|
| `search_products` | Søk hos Oda, Meny, OBS. Fuzzy-ranked via rapidfuzz. |
| `compare_prices` | Top-1 result per store + normalized name |
| `get_store_list` | Returns "Oda, Meny, OBS (lokal/tilbudsavis)" |
| `add_to_list` | Add single item to shopping list |
| `add_multiple_to_list` | Batch add (used for screenshot import) |
| `get_list` | Fetch shopping list contents |
| `import_obs_catalog` | Claude vision parses PDF/image → stores in obs_products |

## Key constraints
- No API keys or environment variables required
- Oda and Meny scrapers use plain HTTP with httpx
- OBS data is stored in SQLite, never scraped live — import via Claude vision + `import_obs_catalog` MCP tool
- `streamlit>=1.35` required for `on_select="rerun"` in `st.dataframe`
- `rapidfuzz>=3.0` is in `requirements.txt` and used in `mcp_server.py`

## Gotchas
- `handleliste` session state is `list[dict]`, not `list[str]` — code that treats it as strings will break
- `split_name_variant` does NOT extract percentages (0,5%, 3,5%) — they stay in the product name
- `remove_item()` accepts `item_id=` for precise deletion; falls back to product_name match if None
- SQLite auto-migration runs on every `import db` — safe to add new ALTER TABLE statements in `_init()`
- Import paths in `mcp_server.py` use `scrapers.oda` and `scrapers.meny` directly (not via `scrapers/__init__.py`)
- OBS import requires Claude vision to parse the ad — the MCP tool receives pre-parsed items, it does not do OCR itself
