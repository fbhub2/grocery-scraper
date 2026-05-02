# Neste steg

> Én ting. Gjør denne ferdig før du åpner BACKLOG.md.

---

## Nå: `feature/product-persistence` (STEG 3 av 10)

**Branch:** `feature/product-persistence`
**Mål:** Scrapers lagrer produkter i DB etter søk. `fetch_price()` på oda.py og meny.py.

### Sjekkliste
- [ ] Opprett branch `feature/product-persistence`
- [ ] `scrapers/oda.py`: kall `db.ensure_store("oda")` + `db.upsert_product()` + `db.upsert_normal()` for hvert søkeresultat
- [ ] `scrapers/meny.py`: samme mønster
- [ ] `scrapers/oda.py`: `fetch_price(product_id: str) -> float | None` (async, httpx)
- [ ] `scrapers/meny.py`: samme
- [ ] `tests/test_scrapers.py`: mock HTTP-svar (aldri kall ekte API)
- [ ] `python -m pytest tests/ -v` → alt grønt
- [ ] Merge til main

### Etter det: `feature/price-fetch-task` (STEG 4)
Se BACKLOG.md for detaljer.

### Merk: `feature/google-auth` (STEG 5) er BLOKKERT
Krever at du setter opp Google Cloud Console manuelt.
Se BACKLOG.md STEG 5 for instruksjoner.

---

## Overordnet veikart

| Steg | Branch                      | Avhenger av | Status   |
|------|-----------------------------|-------------|----------|
| 1    | `feature/db-foundation`     | —           | ✅ Ferdig |
| 2    | `feature/normalization`     | 1           | ✅ Ferdig |
| 3    | `feature/product-persistence`| 1+2        | ⏳ Neste  |
| 4    | `feature/price-fetch-task`  | 1+2+3       | 📋 Plan   |
| 5    | `feature/google-auth`       | 1 + .env ⚠️ | 🔒 Blokkert |
| 6    | `feature/per-user-isolation`| 5           | 🔒 Blokkert |
| 7    | `feature/shopping-list`     | 1+2+5+6     | 📋 Plan   |
| 8    | `feature/watchlist`         | 1+2+4+5+6  | 📋 Plan   |
| 9    | `feature/price-history-ui`  | 1+3+4       | 📋 Plan   |
| 10   | `feature/normalization-ui`  | 2+5+6       | 📋 Plan   |
| —    | `fix/search-ux`             | —           | 📋 Plan   |
| —    | `fix/price-baseline`        | —           | 📋 Plan   |
| —    | `fix/price-arrow-semantics` | —           | 📋 Plan   |
