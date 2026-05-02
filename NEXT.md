# Neste steg

> Én ting. Gjør denne ferdig før du åpner BACKLOG.md.

---

## Nå: `feature/price-fetch-task` (STEG 4 av 10)

**Branch:** `feature/price-fetch-task`
**Mål:** Fullføre `tasks.py run_price_fetch()` med threshold-sjekk og UI-checkbox "Overvåk".

### Sjekkliste
- [ ] Opprett branch `feature/price-fetch-task`
- [ ] `db.py`: `add_to_price_fetch()`, `remove_from_price_fetch()`, `get_price_fetch_products()` — allerede implementert i STEG 1
- [ ] `tasks.py`: `run_price_fetch()` — hent pris via riktig scraper, lagre i `product_price_history`, sjekk watchlist-terskel
- [ ] `app.py`: checkbox "Overvåk" per rad i produkttabell (kobler til `price_fetch`-tabellen)
- [ ] `tests/test_tasks.py`: tester for `run_price_fetch()` med mockete scrapers
- [ ] `python -m pytest tests/ -v` → alt grønt
- [ ] Merge til main

### Etter det: `feature/google-auth` (STEG 5) — BLOKKERT
Krever `.env` med Google-credentials fra deg.

### Merk: `feature/google-auth` (STEG 5) er BLOKKERT
Krever at du setter opp Google Cloud Console manuelt.
Se BACKLOG.md STEG 5 for instruksjoner.

---

## Overordnet veikart

| Steg | Branch                      | Avhenger av | Status   |
|------|-----------------------------|-------------|----------|
| 1    | `feature/db-foundation`     | —           | ✅ Ferdig |
| 2    | `feature/normalization`     | 1           | ✅ Ferdig |
| 3    | `feature/product-persistence`| 1+2        | ✅ Ferdig |
| 4    | `feature/price-fetch-task`  | 1+2+3       | ⏳ Neste  |
| 5    | `feature/google-auth`       | 1 + .env ⚠️ | 🔒 Blokkert |
| 6    | `feature/per-user-isolation`| 5           | 🔒 Blokkert |
| 7    | `feature/shopping-list`     | 1+2+5+6     | 📋 Plan   |
| 8    | `feature/watchlist`         | 1+2+4+5+6  | 📋 Plan   |
| 9    | `feature/price-history-ui`  | 1+3+4       | 📋 Plan   |
| 10   | `feature/normalization-ui`  | 2+5+6       | 📋 Plan   |
| —    | `fix/search-ux`             | —           | 📋 Plan   |
| —    | `fix/price-baseline`        | —           | 📋 Plan   |
| —    | `fix/price-arrow-semantics` | —           | 📋 Plan   |
