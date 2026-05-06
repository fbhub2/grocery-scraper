# Backlog – grocery-scraper / Prissammenligning

Prioritert liste. Øverst = viktigst.

---

## ✅ Ferdig (v2.x — mai 2026)

### Grunnstruktur (v1.x)
- Oda + Meny scraper (httpx), CLI (main.py), Streamlit (app.py)
- SQLite handleliste, produktbilder, prishistorikk, prisvarsel

### STEG 1–6 · DB, normalisering, persistens, pris-task, Google Auth, bruker-isolasjon ✅
### STEG 7 · `feature/shopping-list` ✅ — handleliste-UI (v2.0)
### STEG 8 · `feature/watchlist` ✅ — varslingsliste med terskeltyper
### STEG 9 · `feature/price-history-ui` ✅ — linjediagram, statistikk, rådata
### STEG 10 · `feature/normalization-ui` ✅ — data_editor med custom navn
### STEG 11 · `feature/kassal-integration` ✅ — Kassal.app API + markedspris-badge

### Bugfikser (mai 2026)
- `fix/admin-view`, `fix/streamlit-cloud-auth`, `fix/scraper-dedup`
- `fix/search-ux` (ISSUE-02), `fix/price-baseline` (ISSUE-03), `fix/price-arrow-semantics` (ISSUE-06)
- `bugfix/search-improvements`: EAN i price_history, matchet produkt i handleliste, ⭐ i søketabell

### STEG 12 · `feature/single-product-view` ✅ mai 2026
- [x] Velg 1 rad i søketabell → "🔍 Vis detaljer →"
- [x] Detaljvisning: alle butikker sortert på pris, billigst-highlight, prishistorikk-graf
- [x] Volumfiltrering og relevanssfilter (eliminerer off-topic treff)
- [x] Kassal-dedup: hopper over butikker vi har direkte scraper-data for

### `feature/butikk-innstillinger` ✅ mai 2026
- [x] `user_settings`-tabell + `get/set_user_setting()`
- [x] Sidebar-toggle "Vis fysiske butikker" (Kassal), lagret per bruker

### `feature/normalization-ux` ✅ mai 2026
- [x] Søk normaliserer query via `normalize_search_term()` før scrapers kalles
- [x] Kassal-resultater integrert i kombinert søketabell (ikke lenger separat ekspander)
- [x] Normaliserings-UI: →/⟳-knapper, manuell lagring, ingen tabellhopping
- [x] COMPOUND_SPLITS: 8 → 30+ sammensatte ord
- [x] `_BRAND_WORDS`: Tine, Mills, Stabburet m.fl. strippes fra auto_name

---

## 🔴 Aktiv

### STEG 13 · `feature/family-mode` ✅ mai 2026
- [x] `db.py` — `list_member`-tabell: `(list_id, user_id, role owner/member)`
- [x] `db.py` — `share_token` på `shopping_list` (migrert, unik indeks)
- [x] `db.py` — `get_shopping_lists()` returnerer egne + delte lister med `my_role` og `owner_name`
- [x] `db.py` — `add/remove_list_member()`, `get_list_members()`, `get_user_by_email()`, `get_or_create_share_token()`, `get_list_by_share_token()`
- [x] `app.py` — `?join=<token>` ved oppstart → automatisk member + navigerer til listen
- [x] `app.py` — 👥-ikon på delte lister, "(delt av X)" + "Forlat"-knapp for member-lister
- [x] `app.py` — "👥 Del liste"-ekspander: del-URL (kopiervennlig), inviter via e-post, vis/fjern members
- [x] Kun eier kan slette liste, administrere members og generere del-lenke

---

## 📋 Planlagt

### STEG 14 · `feature/obs-import-v2`
- OBS-tilbudsavis: automatisk refresh (tasks.py), utløpsdato-håndtering
- MCP grocery-scraper laster ikke i Claude Desktop (Electron-problem)

### STEG 15 · `feature/streamlit-cloud-deploy`
- Push main til Streamlit Cloud, verifiser auth og secrets

---

## 🐛 Kjente bugs (åpne)
- [ ] **MCP** — grocery-scraper-server laster ikke i Claude Desktop (Electron-spawning)
- [ ] **ISSUE-07** — Seleksjonsmodell på feil abstraksjonsnivå: SKU vs. kategori

---

## 🪦 Parkert
- ~~Rema 1000~~ — API ikke-funksjonelt
- ~~Supabase~~ — SQLite foretrekkes
