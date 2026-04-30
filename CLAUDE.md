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
  mcp_server.py        # MCP-server (ferdig implementert)
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
- `rapidfuzz>=3.0` er i requirements.txt og brukes i `mcp_server.py` for fuzzy-ranking
- Sjekk alltid faktisk filstruktur med `dir` / `Get-ChildItem` før du antar importstier

## Hva Claude Code må gjøre ved oppstart
1. Les denne filen
2. Sjekk hvilke filer som faktisk finnes (`Get-ChildItem -Recurse`)
3. Ikke anta at en feature er implementert — verifiser i koden

## Git-workflow
```powershell
git checkout -b feature/<navn>   # alltid branch først
claude "<oppgave>"
git diff main
git merge feature/<navn>
```

## Viktig om datamodell
- `handleliste` i Streamlit session state er `list[dict]` (fulle db-rader) — **ikke** `list[str]`
- `db.remove_item()` tar `item_id=` for presis sletting; faller tilbake på produktnavn
- OBS-data importeres via `import_obs_catalog` MCP-tool (Claude vision parser PDF/bilde) — ikke live scraping
- `split_name_variant()` beholder prosent-tokens (0,5%, 3,5%) i produktnavnet

## Kjente gotchas
- Ikke godkjenn `/init`-diff uten å lese den — `/init` har fjernet viktige seksjoner tidligere
- Store refaktoringer: bruk alltid `--plan` først
- Kontekst over 70%: kjør `/compact`
- `streamlit>=1.35` kreves for `on_select="rerun"` i `st.dataframe`
