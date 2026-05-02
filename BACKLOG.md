# Backlog – grocery-scraper / Prissammenligning

Prioritert liste. Øverst = viktigst. Spec: GROCERY_SCRAPER_SPEC.md

---

## 🔴 Aktiv (neste sprint — v2.0)

### STEG 1 · `feature/db-foundation`
- [ ] `db.py` — alle nye tabeller: `store`, `product`, `normal`, `user_normal`, `user`,
  `price_fetch`, `product_price_history`, `shopping_list`, `shopping_list_item`,
  `watchlist`, `search_history`
- [ ] Behold eksisterende funksjoner og tabeller (brukes av MCP-server og app.py)
- [ ] `ensure_store()`, `upsert_product()`, `get_products()`
- [ ] `upsert_normal()`, `get_display_name()`, `list_normals()`
- [ ] `ensure_user()`, `get_user_id()`
- [ ] `save_price()`, `get_price_history_v2()`
- [ ] Oppdater `tests/conftest.py` og `tests/test_db.py`

### STEG 2 · `feature/normalization`
- [ ] `normalize.py` — `auto_normalize()` med COMPOUND_SPLITS
- [ ] `normalize.py` — `resolve_name()` (eneste funksjon UI kaller for produktnavn)
- [ ] `normalize.py` — `check_threshold()` for varslings-logikk
- [ ] `tasks.py` (grunnstruktur) — `run_auto_normalize()`
- [ ] `tests/test_normalize.py` fra spec seksjon 9
- [ ] Fikser ISSUE-01 og ISSUE-04 (duplikate produktnavn)

### STEG 3 · `feature/product-persistence`
- [ ] Scrapers kobles til DB etter søk: `upsert_product()` per resultat
- [ ] `scrapers/oda.py` + `scrapers/meny.py` — `fetch_price(product_id)` async

### STEG 4 · `feature/price-fetch-task`
- [ ] `db.py` — `add_to_price_fetch()`, `remove_from_price_fetch()`, `get_price_fetch_products()`
- [ ] `tasks.py` — `run_price_fetch()` med threshold-sjekk
- [ ] UI-checkbox "Overvåk" per rad i produkttabell
- [ ] `tests/test_tasks.py` fra spec seksjon 9

---

## 🟡 Planlagt (v2.1 — krever manuell Google Cloud-setup av bruker)

### STEG 5 · `feature/google-auth` ⚠️ BLOKKERT
- [ ] **MANUELL FORUTSETNING:** Google Cloud Console → OAuth 2.0 Client ID
  - Redirect URI: `http://localhost:8501/oauth/callback`
  - Legg Client ID + Secret i `.env`
- [ ] `.env` + `.gitignore` (aldri commit .env)
- [ ] `requirements.txt` — legg til `authlib>=1.3`, `python-dotenv>=1.0`
- [ ] `auth.py` — `get_auth_url()`, `exchange_code_for_user()`, `require_login()`
- [ ] `db.py` — `ensure_user()`, `get_user_id()`
- [ ] `main.py` — `require_login()` øverst + sidebar med brukerinfo
- [ ] `tests/test_auth.py` fra spec seksjon 9

### STEG 6 · `feature/per-user-isolation`
- [ ] `db.py` — `user_normal`-tabell, `set_custom_name()`
- [ ] Alle bruker-spesifikke funksjoner tar `user_id`-parameter
- [ ] `price_fetch` kobles til `user_id`

---

## 🔵 Planlagt (v2.2)

### STEG 7 · `feature/shopping-list`
- [ ] `db.py` — `create_shopping_list()`, `get_shopping_lists()`, `get_shopping_list_items()`
- [ ] `db.py` — `add_to_shopping_list()`, `toggle_item_checked()`, `delete_shopping_list()`
- [ ] `main.py` — redesignet seleksjonsmodell: gruppe-kort (IKKE checkbox-tabell)
- [ ] Volum-velger + antall-velger i "Legg til"-dialog
- [ ] Fikser ISSUE-05 og ISSUE-07

### STEG 8 · `feature/watchlist`
- [ ] `db.py` — `add_to_watchlist()`, `get_watchlist()`, `mark_watchlist_triggered()`
- [ ] `tasks.py` — watchlist-sjekk i `run_price_fetch()`
- [ ] `main.py` — varslingsliste UI med fargestatus (🟡🟢⚫)
- [ ] ⭐-knapp + terskel-dialog

### STEG 9 · `feature/price-history-ui`
- [ ] `db.py` — `get_price_history_v2(product_id)`
- [ ] `main.py` — `st.line_chart()` per produkt, én linje per butikk

### STEG 10 · `feature/normalization-ui`
- [ ] `main.py` — "Normalisering"-tab: original_name | auto_name | custom_name (editerbar)

---

## 🔧 Bug-fixes (kan tas parallelt)

- [ ] **`fix/search-ux`** (ISSUE-02) — Fjern antall-felt fra søkeskjema, flytt til "Legg til"-dialog
- [ ] **`fix/price-baseline`** (ISSUE-03) — Baseline per product_id+store_id, aldri blande volum
- [ ] **`fix/price-arrow-semantics`** (ISSUE-06) — ↑=dyrere(rødt), ↓=billigere(grønt)

---

## ✅ Ferdig (v1.x)

- [x] **Grunnstruktur** — Oda + Meny scraper via httpx, CLI (`main.py`), Streamlit (`app.py`)
- [x] **Handleliste + UI-forbedringer** — SQLite handleliste, legg til/fjern varer
- [x] **SQLite-lagring** (`db.py`) — tabeller, `remove_item(item_id=)`, auto-migrering
- [x] **Produktnavn-normalisering** (`normalize.py`) — `normalize_search_term()`, `parse_product_name()`
- [x] **OBS tilbudsavis-import** — `import_obs_catalog` MCP-tool lagrer i SQLite
- [x] **MCP-server** (`grocery_scraper_mcp.py`) — 7 verktøy, stdio transport
- [x] **Søkeresultater-tabell** — butikk-multiselect, sortering, radseleksjon
- [x] **Volume-matching** — `_best_product()`, enhetspris per butikk
- [x] **Produktbilder** (PR #1) — `image_url` fra Oda og Meny
- [x] **Prishistorikk** (PR #2) — `price_history`-tabell, trend-kolonne
- [x] **Prisvarsel** (PR #3) — `st.success()` banner + sidebar-badge

---

## 🪦 Parkert

- ~~Kassal API~~ — ikke i bruk
- ~~Supabase~~ — overkill, SQLite foretrekkes
- ~~Rema 1000~~ — API ikke-funksjonelt

---

## 🐛 Kjente bugs

- [ ] **MCP grocery-scraper laster ikke i Claude Desktop** — server virker isolert, problem i Electron-prosess-spawning
- [ ] **ISSUE-01** — Manglende normalisering: samme produkt vises som 3–5 rader (fix: STEG 2)
- [ ] **ISSUE-02** — Antall på søk-nivå er semantisk feil (fix: `fix/search-ux`)
- [ ] **ISSUE-03** — Prisendring-baseline er feil volum (fix: `fix/price-baseline`)
- [ ] **ISSUE-06** — Prisendring-pil er visuelt inkonsistent (fix: `fix/price-arrow-semantics`)
- [ ] **ISSUE-07** — Seleksjonsmodell på feil abstraksjonsnivå: SKU vs. kategori (fix: STEG 7)
