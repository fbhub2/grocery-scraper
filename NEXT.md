# Neste steg

> Én ting. Gjør denne ferdig før du åpner BACKLOG.md.

---

## Nå: `feature/normalization` (STEG 2 av 10)

**Branch:** `feature/normalization`
**Mål:** `auto_normalize()`, `resolve_name()`, `check_threshold()` i normalize.py + `tasks.py`

### Sjekkliste
- [ ] Opprett branch `feature/normalization`
- [ ] `normalize.py`: `auto_normalize()` med COMPOUND_SPLITS (lowercase, CamelCase, volum-normalisering)
- [ ] `normalize.py`: `resolve_name()` — kaller `db.get_display_name()` (eneste UI-funksjon for produktnavn)
- [ ] `normalize.py`: `check_threshold()` for varslings-logikk
- [ ] `tasks.py` (grunnstruktur): `run_auto_normalize()`
- [ ] Oppdater `tests/test_normalize.py` med tester fra spec seksjon 9
- [ ] `python -m pytest tests/ -v` → alt grønt
- [ ] Merge til main

### Etter det: `feature/product-persistence` (STEG 3)
Se BACKLOG.md for detaljer.

### Merk: `feature/google-auth` (STEG 5) er BLOKKERT
Krever at du setter opp Google Cloud Console manuelt.
Se BACKLOG.md STEG 5 for instruksjoner.

---

## Overordnet veikart

| Steg | Branch                      | Avhenger av | Status   |
|------|-----------------------------|-------------|----------|
| 1    | `feature/db-foundation`     | —           | ✅ Ferdig |
| 2    | `feature/normalization`     | 1           | ⏳ Neste  |
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
