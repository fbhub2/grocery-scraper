# Neste steg

> Én ting. Gjør denne ferdig før du åpner BACKLOG.md.

---

## ✅ STEG 9 implementert — `feature/price-history-ui` (mai 2026)

Branch klar for test. Ikke merget til dev/main ennå.

**Test manuelt:**
1. `streamlit run app.py`
2. Søk priser for en handleliste (for å generere historikkdata)
3. Gå til 📈 Prishistorikk i sidebar
4. Velg et produkt → sjekk linjediagram og statistikk-metrics
5. Endre "Dager tilbake"-slider

---

## Nå: `feature/normalization-ui` (STEG 10)

Normalisering-tab — vis original_name | auto_name | custom_name (editerbar).

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
| 7    | `feature/shopping-list`      | ✅ Ferdig    |
| 8    | `feature/watchlist`          | ✅ Ferdig    |
| 9    | `feature/price-history-ui`   | ⏳ Test      |
| 10   | `feature/normalization-ui`   | 📋 Plan      |
| —    | `fix/search-ux`              | 📋 Plan      |
| —    | `fix/price-baseline`         | 📋 Plan      |
| —    | `fix/price-arrow-semantics`  | 📋 Plan      |
