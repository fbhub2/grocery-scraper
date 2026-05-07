# grocery-scraper – Brief til Claude Code

## Hva dette er
Prissammenligner for norske dagligvarebutikker. Skraper Oda og Meny direkte via HTTP — ingen API-nøkler, ingen Kassal, ingen miljøvariabler nødvendig.

**GitHub:** `fbhub2/grocery-scraper`
**Lokasjon:** `C:\mittprosjekt`

## Arkitektur
```
mittprosjekt/
  main.py              # CLI-inngangspunkt
  app.py               # Streamlit web-app
  db.py                # SQLite-lag (handleliste + OBS-produkter)
  normalize.py         # normalize_search_term(), parse_product_name()
  grocery_scraper_mcp.py  # MCP-server (ferdig implementert)
  grocery.db           # SQLite-database (ikke i git)
  scrapers/
    oda.py             # Oda-scraper (direkte HTTP via httpx)
    meny.py            # Meny-scraper (direkte HTTP via httpx)
    base.py            # Product-dataclass, split_name_variant()
    rema.py            # FINNES MEN BRUKES IKKE — API er ikke-funksjonelt
  BACKLOG.md           # Prioritert oppgaveliste
  NEXT.md              # Neste konkrete steg
  requirements.txt
```

## Viktige regler
- Oda og Meny bruker **ren HTTP med httpx** — ikke selenium, ikke playwright
- **Rema 1000:** `scrapers/rema.py` finnes men kobles IKKE inn — `rema.no/api/products` er ikke-funksjonelt
- **Ingen Kassal API** — tidligere vurdert, ikke i bruk
- `rapidfuzz>=3.0` er i requirements.txt og brukes i `grocery_scraper_mcp.py` for fuzzy-ranking
- Sjekk alltid faktisk filstruktur med `dir` / `Get-ChildItem` før du antar importstier

## Hva Claude Code må gjøre ved oppstart
1. Les denne filen
2. Sjekk hvilke filer som faktisk finnes (`Get-ChildItem -Recurse`)
3. Ikke anta at en feature er implementert — verifiser i koden

## Git-arbeidsflyt

### Branch-struktur
- `main` — produksjon, kjøres av Streamlit Cloud. **ALDRI** commit eller merge hit direkte.
- `dev` — aktiv utviklingsbranch. All ny kode samles her.
- `feature/*` og `bugfix/*` — kortlivede branches, merges inn i `dev` (ikke main).

### Regler — VIKTIG
- Før du starter arbeid: sjekk at vi er på `dev` eller en feature-branch
- Hvis vi er på `main`: bytt til `dev` før du gjør noe som helst
- **ALDRI merge noe som helst uten at brukeren eksplisitt sier "ja, merge"** — ikke "push til X" eller "test på X" er godkjenning for merge
- **ALDRI foreslå merge til `main`** — det er en bevisst release-beslutning brukeren tar selv, uten påminnelse
- Etter en commit: push til **current branch**, så STOPP og spør hva brukeren vil gjøre
- Ikke kjed flere git-operasjoner i én kommando uten eksplisitt godkjenning (f.eks. merge + push er to separate beslutninger)

## Viktig om datamodell
- Handleliste (v2.0): `db.get_shopping_lists(user_id)` + `db.get_shopping_list_items(list_id)` — ikke v1.x `get_list()`
- `_list_name()` i app.py er v1.x-relikt (brukt av MCP) — ny UI bruker v2.0 `shopping_list`-tabellen
- `split_name_variant()` beholder prosent-tokens (0,5%, 3,5%) i produktnavnet — prosent er produkttype, ikke mengde
- OBS-data importeres via `import_obs_catalog` MCP-tool — ikke live scraping

## UI/UX-analyse med Playwright MCP

Playwright MCP er satt opp for interaktiv UI-testing og analyse direkte mot kjørende app.

### Når brukes det
| Oppgave | Verktøy | Token-kostnad |
|---|---|---|
| Bug-fix (finne feilmelding, sjekke state) | DOM + console — ingen screenshot | Lav |
| Bug-find (navigere, klikke, utforske flyt) | Klikk + DOM | Lav–middels |
| UX-analyse (visuell layout, kontrast, flow) | Målrettet screenshot | Middels |

Ta aldri full-side screenshot uten grunn — bruk heller `locator`-baserte screenshots av én komponent.

### Forutsetning
Appen må kjøre lokalt:
```bash
streamlit run app.py   # → http://localhost:8501
```

### Konfigurasjon
- **Claude Code:** `.mcp.json` i prosjektrot (sjekket inn i git)
- **Claude Desktop:** `AppData/Roaming/Claude/claude_desktop_config.json`
- Browser: Chromium, headless
- Package: `@playwright/mcp@0.0.74` (global npm)
- Playwright: v1.59.1

### Typiske instruksjoner til meg
```
# Bug-find
"Gå til localhost:8501, logg inn, åpne handleliste, søk etter 'melk' og sjekk at handleplan viser produktnavn"

# UX-analyse
"Ta screenshot av søkeresultattabellen og vurder lesbarhet og kolonnebredder"

# Regresjonstest
"Verifiser at familie-delingskode-flyten fungerer — opprett familie, kopier kode, bli med"
```

### Reinstallasjon ved behov
```bash
npm install -g @playwright/mcp
npx playwright install chromium
```

## Kjente gotchas
- Ikke godkjenn `/init`-diff uten å lese den — `/init` har fjernet viktige seksjoner tidligere
- Store refaktoringer: bruk alltid `--plan` først
- Kontekst over 70%: kjør `/compact`
- `streamlit>=1.35` kreves for `on_select="rerun"` i `st.dataframe`
