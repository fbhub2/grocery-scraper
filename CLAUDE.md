# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

Norwegian grocery price comparison tool. Scrapes Oda, Meny, and Rema 1000 via direct HTTP (no API keys needed). Two entry points: a CLI (`main.py`) and a Streamlit web app (`app.py`).

## Running the app

```bash
# Streamlit web UI
streamlit run app.py

# CLI
python main.py "melk" -n 5 -o resultater.json
```

Dependencies: `pip install -r requirements.txt` (httpx, streamlit, pandas).

## Architecture

### Data flow
1. User search → `scrapers/<store>.py` fires an HTTP GET to the store's undocumented JSON API
2. Raw API response parsed into `Product` dataclass (defined in `scrapers/base.py`)
3. `split_name_variant()` in `base.py` strips size/volume tokens from product names so they can be shown on a separate line in the UI
4. Results returned to caller (`app.py` or `main.py`) which renders or prints them

### Scrapers (`scrapers/`)

Each scraper exposes a single `search(query, limit) -> list[Product]` function, re-exported from `scrapers/__init__.py` as `{store}_search`.

| File | Store | API endpoint |
|------|-------|-------------|
| `oda.py` | Oda | `https://oda.com/api/v1/search/mixed/` |
| `meny.py` | Meny | `https://platform-rest-prod.ngdata.no/api/episearch/1300/autosuggest` |
| `rema.py` | Rema 1000 | `https://www.rema.no/api/products` |

### `scrapers/base.py`
- `Product` dataclass: `name`, `price`, `unit_price`, `url`, `variant`
- `split_name_variant(full)`: extracts size tokens (e.g. `1,75 l`, `540 g`, `0,5%`) from a product string, returns `(clean_name, variant_string | None)`

### `app.py` (Streamlit)
- Session state keys: `handleliste`, `search_results`, `search_errors`, `last_query`, `liste_resultater`
- Shopping list persisted to `handleliste.json` in the project root
- "Søk alle på listen" fetches top-1 result per item and builds a cross-store price comparison table with an optimal-cart calculation

### MCP server
`.mcp.json` configures a local MCP server (`mcp_server.py`) for use with Claude Code and Claude Desktop. See `mcp_task.md` for the implementation plan.

## Key constraints
- No API keys or environment variables required
- `rapidfuzz` is not in `requirements.txt` yet — add `rapidfuzz>=3.0` before implementing fuzzy search
- Import paths in `mcp_server.py` must match the actual `scrapers/` layout

## Viktige regler
- Ingen API-nøkler eller miljøvariabler er nødvendig
- Oda og Meny scrapers bruker ren HTTP med httpx
- OBS-data lagres lokalt i SQLite, ikke scraped live
- rapidfuzz er IKKE i requirements.txt ennå — legg til ved fuzzy-søk-implementasjon
- Streamlit brukes for UI, støtter både PC og mobil

## Hva Claude Code må gjøre ved oppstart
1. Les `mcp_task.md` for fullstendig implementeringsplan
2. Sjekk faktisk filstruktur før du antar importstier
3. Kjør `cat requirements.txt` for å verifisere avhengigheter

## Kjente gotchas
- Importstier i mcp_server.py MÅ matche faktisk filstruktur (sjekk scrapers/)
- SQLite db.py må opprettes hvis den ikke finnes
- OBS bruker Claude vision — ikke pytesseract eller annen OCR-lib
- rapidfuzz: legg til i requirements.txt før bruk: `rapidfuzz>=3.0`
