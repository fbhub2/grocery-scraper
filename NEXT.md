# Neste steg

> Én ting. Gjør denne ferdig før du åpner BACKLOG.md.

---

## ✅ STEG 5 ferdig — `feature/google-auth` (mai 2026)

129 tester grønne. Branch pushet til GitHub.
**Ikke merget til main** — krever at du tester innlogging manuelt i nettleseren.

### Slik tester du auth:
```
streamlit run app.py
```
Åpne http://localhost:8501 — du skal se en "Logg inn med Google"-knapp.

## Nå: `feature/per-user-isolation` (STEG 6)

**Avhenger av:** STEG 5 er ute i review.
**Kan starte nå** — endringer er bakoverkompatible med eksisterende DB.

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
