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

### STEG 7 · `feature/shopping-list` ✅ mai 2026
- [x] `db.py` — alle handleliste-funksjoner (fra STEG 1) + `remove_shopping_list_item()`
- [x] `app.py` — sidebar navigasjon: Søk / Handlelister
- [x] `app.py` — Handlelister-seksjon: oversikt, opprett/slett/åpne liste
- [x] `app.py` — Åpen liste: varer med avhaking, antall, merknad, fjern
- [x] `app.py` — "Søk priser for alle varer" → prissammenligning med optimal sum
- [x] `app.py` — "Legg i liste"-popover i søk: velg liste + antall

### STEG 8 · `feature/watchlist` ✅ mai 2026
- [x] `db.py` — alle watchlist-funksjoner (fra STEG 1), `tasks.py` terskel-sjekk (fra STEG 4)
- [x] `app.py` — ⭐ Varsle meg-popover i søkeresultater: terskeltype + verdi
- [x] `app.py` — Varslingsliste-seksjon: 🟢 truffet / 🟡 venter / ⚫ inaktive
- [x] `app.py` — Truffet-handling: Legg i liste + Ignorer (reset til venter)
- [x] Sidebar-nav viser antall truffet varsler som badge

### STEG 9 · `feature/price-history-ui` ✅ mai 2026
- [x] `db.py` — `get_products_with_history()`, `get_price_history()` (bruker v1.x `price_history`)
- [x] `app.py` — `_show_prishistorikk()`: selectbox, slider, linjediagram per butikk, statistikk-metrics, rådata-tabell
- [x] Sidebar-nav + routing koblet inn

### Bugfikser · `bugfix/search-improvements` ✅ mai 2026
- [x] Kassal-priser lagres til `price_history` med EAN
- [x] Handleliste prissammenligning viser matchet produktnavn per butikk
- [x] Søketabell: ⭐-kolonne for varslingsliste-status + "Varsle valgte"-knapp

### STEG 11 · `feature/kassal-integration` ✅ mai 2026
- [x] `scrapers/kassal.py` — Kassal.app API-scraper (graceful fallback uten nøkkel)
- [x] `scrapers/base.py` — `ean` og `store_name` felt på Product
- [x] `db.py` — `ean`-kolonne i `price_history`, `get_market_avg()`
- [x] `app.py` — "Andre butikker via Kassal"-ekspander i søk
- [x] `app.py` — Markedspris-badge på produktkort ("X% under/over snitt")
- [x] `app.py` — "Optimal handleplan" i handleliste-resultater

### STEG 10 · `feature/normalization-ui` ✅ mai 2026
- [x] `db.py` — `list_normals_with_custom(user_id, filter)` — join normal + user_normal
- [x] `app.py` — `_show_normalisering()`: filter, st.data_editor med Original | Auto | Ditt navn
- [x] Auto-lagring ved celleendring, slett custom ved tomt felt
- [x] Sidebar-nav + routing koblet inn

---

## 🔧 Bug-fixes (kan tas parallelt)

- [x] **`fix/admin-view`** — Admin-panel inline i app.py, admin-knapp skjult for ikke-admin, email ikke mailto, OBS-seksjon fjernet
- [x] **`fix/streamlit-cloud-auth`** — `auth.py` leser fra `st.secrets` som fallback, `.strip()` på alle OAuth-verdier
- [x] **`fix/scraper-dedup`** — `seen_ids`-dedup i Oda og Meny scrapers
- [x] **`fix/search-ux`** (ISSUE-02) — Fjern antall-felt fra søkeskjema, hardkodet limit=5
- [x] **`fix/price-baseline`** (ISSUE-03) — Baseline per product_name+store+volume, aldri blande volum
- [x] **`fix/price-arrow-semantics`** (ISSUE-06) — 🔴 ↑ = dyrere, 🟢 ↓ = billigere

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

### STEG 12 · `feature/single-product-view` ✅ mai 2026
- [x] `app.py` — `_show_product_detail()`: alle butikker + markedspris + prishistorikk på én side
- [x] `app.py` — 1 rad valgt i søketabell → "🔍 Vis detaljer →"-knapp
- [x] `app.py` — Handlinger: legg i liste + varsle meg direkte fra detaljvisning
- [x] `app.py` — Tilbake til søk uten å miste søkeresultater

---

## 🪦 Parkert

- ~~Kassal API~~ — ikke i bruk
- ~~Supabase~~ — overkill, SQLite foretrekkes
- ~~Rema 1000~~ — API ikke-funksjonelt

---

## 🐛 Kjente bugs

- [ ] **MCP grocery-scraper laster ikke i Claude Desktop** — server virker isolert, problem i Electron-prosess-spawning
- [x] **ISSUE-01** — Manglende normalisering: samme produkt vises som 3–5 rader (fix: STEG 2)
- [x] **ISSUE-02** — Antall på søk-nivå er semantisk feil (hardkodet limit=5)
- [x] **ISSUE-03** — Prisendring-baseline er feil volum (volume-parameter i `get_price_trend`)
- [x] **ISSUE-06** — Prisendring-pil er visuelt inkonsistent (🔴↑ dyrere, 🟢↓ billigere)
- [ ] **ISSUE-07** — Seleksjonsmodell på feil abstraksjonsnivå: SKU vs. kategori (fix: STEG 7)
- [x] **BUG-EAN** — Kassal-priser ble ikke lagret til price_history med EAN (`bugfix/search-improvements`)
- [x] **BUG-HANDLELISTE-PRODUKT** — Prissammenligning i handleliste viste ikke matchet produktnavn (`bugfix/search-improvements`)
- [x] **BUG-WL-STJERNE** — Søketabell viste ikke ⭐ for produkter på varslingsliste (`bugfix/search-improvements`)
