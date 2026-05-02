# Neste steg

> Én ting. Gjør denne ferdig før du åpner BACKLOG.md.

---

## Nå: `feature/db-foundation` (STEG 1 av 10)

**Branch:** `feature/db-foundation`
**Mål:** Ny `db.py` med alle spec-tabeller. Behold eksisterende funksjoner.

### Sjekkliste
- [ ] Opprett branch `feature/db-foundation`
- [ ] Legg til nye tabeller i `db.py` via `CREATE TABLE IF NOT EXISTS`:
  - `store`, `product`, `normal`, `user_normal`, `user`
  - `price_fetch`, `product_price_history`
  - `shopping_list`, `shopping_list_item`, `watchlist`, `search_history`
- [ ] Legg til nye funksjoner (ikke fjern gamle — MCP-server bruker dem)
- [ ] Oppdater `tests/test_db.py` med tester fra spec seksjon 9
- [ ] `python -m pytest tests/test_db.py -v` → alt grønt
- [ ] Oppdater CHANGELOG.md
- [ ] Merge til main

### Etter det: `feature/normalization` (STEG 2)
Se BACKLOG.md for detaljer.

### Merk: `feature/google-auth` (STEG 5) er BLOKKERT
Krever at du setter opp Google Cloud Console manuelt.
Se BACKLOG.md STEG 5 for instruksjoner.

---

## Overordnet veikart

| Steg | Branch                      | Avhenger av | Status   |
|------|-----------------------------|-------------|----------|
| 1    | `feature/db-foundation`     | —           | ⏳ Neste  |
| 2    | `feature/normalization`     | 1           | 📋 Plan   |
| 3    | `feature/product-persistence`| 1+2        | 📋 Plan   |
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
