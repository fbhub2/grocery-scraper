# Arkitekturbeslutninger (Decision Log)

Logg over viktige valg tatt underveis, med begrunnelse.
Formål: hindre at AI (eller du) reverserer beslutninger uten grunn.

---

## DEC-001 · Ingen Kassal API-nøkkel

**Dato:** apr 2026
**Beslutning:** Scrape Oda og Meny direkte via HTTP (httpx), ikke via Kassal aggregator-API
**Begrunnelse:** Eliminerer ekstern avhengighet og API-nøkkelhåndtering
**Konsekvens:** Mer skjør mot layout-endringer hos butikkene, men enklere deploy
**Status:** Gjeldende

---

## DEC-002 · Én fil per butikk i `scrapers/`

**Dato:** apr 2026
**Beslutning:** `scrapers/oda.py`, `scrapers/meny.py` — ikke én monolittisk fil
**Begrunnelse:** Gjør det enkelt å legge til, fjerne eller feilsøke én butikk isolert
**Status:** Gjeldende

---

## DEC-003 · Rema 1000 er ekskludert

**Dato:** apr 2026
**Beslutning:** Ikke implementere Rema-scraper
**Begrunnelse:** `rema.no/api/products` returnerer ikke brukbare data
**Revurder hvis:** Rema åpner et fungerende API
**Status:** Gjeldende

---

## DEC-004 · SQLite fremfor sky-database

**Dato:** apr 2026
**Beslutning:** SQLite (`grocery.db`) for handleliste, OBS-produkter og prishistorikk
**Begrunnelse:** Overkill med Supabase/Postgres for én bruker; SQLite er tilstrekkelig og krever ingen infrastruktur
**Status:** Gjeldende

---

## DEC-005 · OBS-import via Claude Vision, ikke scraping

**Dato:** apr 2026
**Beslutning:** OBS tilbudsavis importeres ved å sende PDF/bilde til Claude (MCP-tool `import_obs_catalog`), ikke live HTTP-scraping
**Begrunnelse:** OBS har ingen strukturert API; Claude Vision gir høy nøyaktighet på katalogparsing
**Konsekvens:** Krever manuell import én gang per uke
**Status:** Gjeldende

---

## DEC-006 · `split_name_variant()` beholder prosenttokens

**Dato:** apr 2026
**Beslutning:** `_SIZE_RE` matcher IKKE `%`-tokens — `"0,5%"` og `"3,5%"` beholdes i produktnavn
**Begrunnelse:** Fettprosent er del av produktidentiteten (f.eks. Tine Lettmelk 0,5%), ikke en mengdeangivelse
**Status:** Gjeldende

---

## DEC-007 · Prishistorikk lagres per søk, ikke per dag

**Dato:** apr 2026
**Beslutning:** `record_price()` kalles hver gang "Søk alle på listen" kjøres — ingen deduplicering på dato
**Begrunnelse:** Enklere implementasjon; `get_price_trend()` henter alltid de to siste datapunktene
**Konsekvens:** Mange kjøringer samme dag gir mange rader, men fungerer korrekt
**Status:** Gjeldende (v1.x — erstattes av DEC-011 i v2.0)

---

## DEC-008 · sqlite3 over SQLAlchemy (v2.0)

**Dato:** mai 2026
**Beslutning:** Bruker sqlite3 (standard lib) — ikke SQLAlchemy, ikke aiosqlite
**Begrunnelse:** Enklere, ingen dependencies, tilstrekkelig for prosjektets størrelse
**Konsekvens:** Manuelle SQL-queries i db.py, synkrone kall — greit for Streamlit

---

## DEC-009 · google_sub som bruker-ID

**Dato:** mai 2026
**Beslutning:** Bruker Google `sub`-claim, ikke e-post, som stabil bruker-ID
**Begrunnelse:** E-post kan endres av bruker. `sub` er stabil livstid.
**Konsekvens:** Alle bruker-oppslag bruker `google_sub`, ikke email

---

## DEC-010 · price_history er global (deles på tvers av brukere)

**Dato:** mai 2026
**Beslutning:** `product_price_history`-tabellen deles på tvers av brukere
**Begrunnelse:** Ingen grunn til å lagre samme pris/dato dobbelt for to brukere
**Konsekvens:** `UNIQUE(product_id, store_id, date)` hindrer duplikater automatisk

---

## DEC-011 · product_price_history (v2) — ny tabell, beholder gammel price_history

**Dato:** mai 2026
**Beslutning:** v2.0 bruker ny tabell `product_price_history` med FK til `product` og `store`.
  Gammel `price_history`-tabell beholdes uendret (brukes av MCP-server og app.py v1)
**Begrunnelse:** `CREATE TABLE IF NOT EXISTS` kan ikke endre schema på eksisterende tabell.
  Rename/migration av live tabell er mot constraint "ingen migrasjoner".
**Konsekvens:** To tabeller med prisdata i overgangsperioden. Gammel fjernes når app.py er erstattet av main.py (v2).

---

## DEC-012 · user_normal over custom_name i normal

**Dato:** mai 2026
**Beslutning:** Per-bruker custom-navn i egen `user_normal`-tabell, ikke i `normal`
**Begrunnelse:** `normal`-tabellen er global. Custom-navn er personlig preferanse.
**Konsekvens:** `get_display_name()` sjekker user_normal → normal.auto_name → original_name

---

## DEC-013 · Handleliste lagrer original_name (kategori), ikke product_id (SKU)

**Dato:** mai 2026
**Beslutning:** `shopping_list_item.original_name` kobler til `normal`-tabellen, ikke `product`
**Begrunnelse:** Brukeren tenker "lettmelk", ikke "Tine Lettmelk 1L fra Oda"
**Konsekvens:** Best-pris-visning gjøres ved oppslag mot siste `product_price_history` for alle matchende produkter

---

## DEC-014 · authlib over streamlit-google-auth

**Dato:** mai 2026
**Beslutning:** Bruker `authlib` direkte for Google OAuth 2.0
**Begrunnelse:** `streamlit-google-auth` er ikke vedlikeholdt på PyPI
**Konsekvens:** Mer kode i `auth.py`, men stabilt og produksjonsklar

---

## DEC-015 · app.py rename til main.py (v2.0)

**Dato:** mai 2026
**Beslutning:** Streamlit-appen heter `main.py` i v2.0. Nåværende `main.py` (CLI) renames til `cli.py`.
**Begrunnelse:** Spec sier `main.py` er Streamlit-inngangspunkt. Konsistens med spec.
**Tidspunkt:** Gjøres i `feature/shopping-list`-branchen (STEG 7) når ny UI-struktur er klar.
