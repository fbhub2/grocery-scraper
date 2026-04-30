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
**Status:** Gjeldende
