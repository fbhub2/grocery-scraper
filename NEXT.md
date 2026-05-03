# Neste steg

> Én ting. Gjør denne ferdig før du åpner BACKLOG.md.

---

## ✅ STEG 7 implementert — `feature/shopping-list` (mai 2026)

Branch klar for test. Ikke merget til main ennå.

**Test manuelt:**
1. `streamlit run app.py`
2. Opprett en ny handleliste
3. Søk etter en vare → "Legg i liste"-popover → velg liste + antall
4. Gå til Handlelister → åpne lista → avhak varer, fjern varer
5. Klikk "Søk priser for alle varer" → sjekk prissammenligning

---

## Nå: `feature/watchlist` (STEG 8)

Varslingsliste — ⭐-knapp i søk, terskel-dialog, varslings-UI.

---

## Overordnet veikart

| Steg | Branch                       | Status      |
|------|------------------------------|-------------|
| 1    | `feature/db-foundation`      | ✅ Ferdig    |
| 2    | `feature/normalization`      | ✅ Ferdig    |
| 3    | `feature/product-persistence`| ✅ Ferdig    |
| 4    | `feature/price-fetch-task`   | ✅ Ferdig    |
| 5    | `feature/google-auth`        | ✅ Ferdig    |
| 6    | `feature/per-user-isolation` | ✅ Ferdig    |
| 7    | `feature/shopping-list`      | ⏳ Test      |
| 8    | `feature/watchlist`          | 📋 Plan      |
| 9    | `feature/price-history-ui`   | 📋 Plan      |
| 10   | `feature/normalization-ui`   | 📋 Plan      |
| —    | `fix/search-ux`              | 📋 Plan      |
| —    | `fix/price-baseline`         | 📋 Plan      |
| —    | `fix/price-arrow-semantics`  | 📋 Plan      |
