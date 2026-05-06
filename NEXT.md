# Neste steg

> Én ting. Gjør denne ferdig før du åpner BACKLOG.md.

---

## ✅ `bugfix/search-improvements` merget til dev (mai 2026)

Tre bugfikser levert:
1. Kassal-priser lagres nå til `price_history` (EAN inkludert)
2. Handleliste prissammenligning viser matchet produktnavn per butikk
3. Søketabell viser ⭐ for produkter på varslingsliste + "Varsle valgte"-knapp

---

## Nå: `bugfix/obs-validity` eller STEG 12

**Kandidater (velg én):**

### A) STEG 12 — `feature/single-product-view`
Kassal.app-inspirert redesign: enkelt produkt → alle butikker på én side.
- Klikk produkt i søkeresultat → åpner detaljvisning
- Alle butikker som selger produktet (via EAN-match)
- Prishistorikk inline
- Kompleks — estimert 2–3 sesjoner

### B) `bugfix/obs-kassal-toggle`
Kassal toggle ("Vis fysiske butikker") fra `feature/butikk-innstillinger`
er committet men ikke merget til dev ennå.

---

## Overordnet veikart

| Steg | Branch                         | Status      |
|------|--------------------------------|-------------|
| 1    | `feature/db-foundation`        | ✅ Ferdig    |
| 2    | `feature/normalization`        | ✅ Ferdig    |
| 3    | `feature/product-persistence`  | ✅ Ferdig    |
| 4    | `feature/price-fetch-task`     | ✅ Ferdig    |
| 5    | `feature/google-auth`          | ✅ Ferdig    |
| 6    | `feature/per-user-isolation`   | ✅ Ferdig    |
| 7    | `feature/shopping-list`        | ✅ Ferdig    |
| 8    | `feature/watchlist`            | ✅ Ferdig    |
| 9    | `feature/price-history-ui`     | ✅ Ferdig    |
| 10   | `feature/normalization-ui`     | ✅ Ferdig    |
| 11   | `feature/kassal-integration`   | ✅ Ferdig    |
| —    | `bugfix/search-improvements`   | ✅ Ferdig    |
| —    | `feature/butikk-innstillinger` | ⏳ Klar, ikke merget til dev |
| 12   | `feature/single-product-view`  | 📋 Plan      |
| 13   | `feature/family-mode`          | 📋 Plan      |
