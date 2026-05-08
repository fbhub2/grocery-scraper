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

### Vedlikehold · mai 2026
- [x] `tasks.py` — `run_auto_normalize(force=True)` overskriv alle auto_name
- [x] `tasks.py` — CLI-flagg `python tasks.py normalize --force`
- [x] Admin-panel — "🔄 Kjør auto-normalisering (force)"-knapp
- [x] 95 eksisterende produktnavn kjørt gjennom ny logikk (compound splits + merkevare-stripping)
- [x] `SHARE_BASE_URL` env-variabel for del-liste-URL (dev: localhost, prod: Streamlit Cloud URL)

---

## 📋 Planlagt

### `feature/ean-core` ✅ klar for merge — mai 2026
- [x] `product.ean` kolonne + indeks (migrasjon)
- [x] `upsert_product()` tar EAN-parameter
- [x] `get_products_by_ean()` og `compare_by_ean()` for kryssbutikk-matching
- [x] Meny-scraper: EAN i Product-objekt og DB
- [x] Kassal-scraper: persisterer til DB med EAN
- [x] Admin: EAN-dekning per butikk + kryssbutikk-treff-tabell
- **Oda:** ingen EAN i API (verifisert) — bruker intern numerisk ID

### `feature/prishistorikk-inline` ✅ klar for merge — mai 2026
- [x] Prishistorikk fjernet fra venstremenyen
- [x] Prishistorikk som collapsbar expander nederst på Søk, Handlelister og Varslingsliste

### `feature/import-handleliste` ✅ klar for merge — mai 2026
- [x] "Importer produkter"-ekspander i aktiv handleliste
- [x] Støtter linjeskift, komma og semikolon som skilletegn
- [x] Kan legge til i aktiv liste eller opprette ny liste

### `feature/produkt-ikoner` — neste sprint
**Mål:** Alle produkter (tabell og kortvisning) får fire handlingsikoner:

| Ikon | Funksjon | Merknad |
|---|---|---|
| 🔔 | Legg til/fjern varsling | Toggle on/off, erstatter `_varsle_meg_popover()` |
| 📋 | Legg til/fjern handleliste | Toggle on/off, erstatter `_legg_til_popover()` |
| 👁️ | Vis produkt i butikk | Åpne produkt-URL i ny fane |
| 🔍 | Søk på dette produktet | Pre-fyller søkefeltet med produktnavnet |

**Teknisk:**
- `st.dataframe()` støtter ikke custom knapper per rad → ikonene går **under tabellen** for valgte rader, og **direkte i kortene** i kortvisningen
- Ny hjelpefunksjon `_produkt_ikoner(name, price, url, key_suffix)` brukes på tvers av alle visningstyper
- ISSUE-07 kan delvis løses her ved å bruke EAN som nøkkel for handleliste-tillegg

### `feature/kassal-inline` — neste sprint
**Mål:** Kassal-resultater vises på lik linje med Oda og Meny overalt.

**Endringer:**
- Fjern "🏪"-prefiks fra Kassal-butikknavn i tabeller (behold som tooltip/badge i stedet)
- Inkluder Kassal-butikker i **optimal handleplan** (kun fysiske butikker om "vis fysiske" er på)
- Kassal søkes parallelt med Oda/Meny i `run_search()` (ikke separat `run_kassal_search()`) når toggle er på
- Brukerinnstilling kontrollerer om Kassal inkluderes i prissammenlignings-tabellen

### `feature/nearest-store` — backlog
**Mål:** Vis hvilken Kassal-butikk som er nærmest brukeren.

**Forutsetninger som må avklares:**
- Kassal API: sjekk om `/stores` eller `/products`-endepunkt returnerer butikkens GPS-koordinater eller adresse
- Geolokasjon: Streamlit støtter ikke browser geolocation nativt — alternativ: postnummer-input fra bruker
- Mulig tilnærming: bruker taster postnummer → lookup mot postnummer→koordinat-tabell → beregn avstand til Kassal-butikker

**Avhenger av:** `feature/kassal-inline`

---

### STEG 14 · `feature/obs-import-v2`
- OBS-tilbudsavis: automatisk refresh (tasks.py), utløpsdato-håndtering
- **Langsiktig:** lage egen Ollama-lokal → MCP → prod-db
  (lokal LLM-agent parser tilbudsaviser og pusher til prod-databasen via MCP-server)

### STEG 15 · `feature/streamlit-cloud-deploy`
- Push main til Streamlit Cloud
- Sett secrets: GOOGLE_CLIENT_ID/SECRET, KASSAL_API_KEY, ADMIN_EMAIL, SHARE_BASE_URL

---

## 🐛 Kjente bugs (åpne)
- [ ] **MCP** — grocery-scraper-server laster ikke i Claude Desktop (Electron-spawning)
- [ ] **ISSUE-07** — Seleksjonsmodell på feil abstraksjonsnivå: SKU vs. kategori

---

## 🗄️ DB-persistens (avventer beslutning)

**Problem:** Streamlit Community Cloud har efemær disk — `grocery.db` slettes ved redeploy/restart.
Data som går tapt: brukere, familier, handlelister, normalisering, varslingsliste, prishistorikk.

**Vurderte alternativer (mai 2026):**

| Alternativ | Kodeendring i db.py | Kostnad | Notat |
|---|---|---|---|
| **Neon PostgreSQL** | ~950 linjer, mekanisk | Gratis | Anbefalt hvis PG velges. Bruk transformasjons-script for ~80%, fiks resten manuelt. Estimat: ½–1 kontekstvindu |
| **Fly.io + persistent volum** | Null | ~$3/mnd | Kun Dockerfile + fly.toml. SQLite uendret. Bytter bort Streamlit Cloud |
| **SQLite Cloud** | Minimal (kun `_conn()`) | Gratis | Drop-in sqlite3-kompatibel. Nyere tjeneste, noe usikkerhet |

**Neon-detaljer hvis valgt:**
- To drivers = to SQL-dialekter → bruk Neon for **begge** miljøer (dev-branch + prod-branch), ikke SQLite lokalt
- Neon støtter DB-branching (som git) — `dev`-branch for lokal test, `main`-branch for prod
- Endringer: `?`→`%s`, `AUTOINCREMENT`→`SERIAL`, `INSERT OR IGNORE`→`ON CONFLICT DO NOTHING`, `lastrowid`→`RETURNING id`, fjern `PRAGMA`, fjern migrasjons-seksjonen

**Beslutning:** Avventer. SQLite beholdes til første prod-release. Revurder etter at driftsbehovet er klart.

---

## 🪦 Parkert
- ~~Rema 1000~~ — API ikke-funksjonelt
- ~~Supabase~~ — SQLite foretrekkes (se DB-persistens over)
