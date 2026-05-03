# Backlog – grocery-scraper / Prissammenligning

Prioritert liste. Øverst = viktigst. Spec: GROCERY_SCRAPER_SPEC.md

---

## ✅ Ferdig (v2.0 — pågående)

### STEG 1 · `feature/db-foundation` ✅ mai 2026
- [x] 11 nye tabeller i `db.py` (v2.0 schema)
- [x] 30+ nye funksjoner: store, product, normal, user, price_history_v2, shopping_list, watchlist
- [x] Alle v1.x-funksjoner beholdt (backward compat)
- [x] 37 nye tester, 71 totalt grønne

---

## 🔴 Aktiv (neste sprint — v2.0)

### STEG 2 · `feature/normalization` ✅ mai 2026
- [x] `normalize.py` — `auto_normalize()` med COMPOUND_SPLITS, CamelCase-split, volum-norm
- [x] `normalize.py` — `resolve_name()` — eneste UI-funksjon for produktnavn
- [x] `normalize.py` — `check_threshold()` — absolutt/relativ/sale
- [x] `tasks.py` — `run_auto_normalize()`, `python tasks.py normalize`
- [x] 26 nye tester, 97 totalt grønne

### STEG 3 · `feature/product-persistence` ✅ mai 2026
- [x] `scrapers/oda.py`: `upsert_product()` + `upsert_normal()` per søkeresultat
- [x] `scrapers/meny.py`: samme mønster, bruker EAN som produkt-ID
- [x] `fetch_price(product_id)` async på begge scrapers (returnerer None ved feil)
- [x] 14 nye tester (mockete HTTP), 111 totalt grønne

### STEG 4 · `feature/price-fetch-task` ✅ mai 2026
- [x] `db.py` — `get_all_price_fetch_products()`, `get_watchlist_by_name()`
- [x] `tasks.py` — `run_price_fetch()` med asyncio.gather + watchlist-terskel-sjekk
- [x] `tests/test_tasks.py` — 15 nye tester (mockete scrapers), 126 totalt grønne

---

## 🟡 Planlagt (v2.1 — krever manuell Google Cloud-setup av bruker)

### STEG 5 · `feature/google-auth` ✅ mai 2026
- [x] `.env` med GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI
- [x] `requirements.txt` — authlib>=1.3, python-dotenv>=1.0
- [x] `auth.py` — `get_auth_url()`, `exchange_code_for_user()`, `require_login()`, `st.secrets`-fallback for Streamlit Cloud
- [x] `app.py` — `require_login()` øverst + brukerinfo i sidebar
- [x] `tests/test_auth.py` — 3 tester, 129 totalt grønne
- [x] Session-persistens via SQLite + `?s=<token>` (overlever F5)
- [x] Merget til main og verifisert i prod (grocery-scraper-bitflow.streamlit.app)

### STEG 6 · `feature/per-user-isolation` ✅ mai 2026
- [x] `app.py` — `_list_name()` returnerer `f"user_{_user_db_id}"` — handleliste er isolert per bruker
- [x] Alle `db.add_item`/`remove_item`/`get_list`-kall bruker `_list_name()`
- [x] Merget til main

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

- [x] **`fix/admin-view`** — Admin-panel inline i app.py, admin-knapp skjult for ikke-admin, email ikke mailto, OBS-seksjon fjernet
- [x] **`fix/streamlit-cloud-auth`** — `auth.py` leser fra `st.secrets` som fallback, `.strip()` på alle OAuth-verdier
- [x] **`fix/scraper-dedup`** — `seen_ids`-dedup i Oda og Meny scrapers
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
