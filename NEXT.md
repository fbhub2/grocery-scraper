# Neste steg

> Én ting. Gjør denne ferdig før du åpner BACKLOG.md.

---

## ✅ STEG 6 ferdig — `feature/per-user-isolation` (mai 2026)

Handleliste er nå isolert per bruker via `_list_name()` = `f"user_{_user_db_id}"`.
Auth, admin-panel og alle bug-fixes merget til main og kjører i prod.

**Prod-URL:** https://grocery-scraper-bitflow.streamlit.app/

---

## Nå: `feature/shopping-list` (STEG 7)

Per spec — redesignet seleksjonsmodell, nye db-funksjoner, volum-velger.

---

## Overordnet veikart

| Steg | Branch                       | Avhenger av | Status      |
|------|------------------------------|-------------|-------------|
| 1    | `feature/db-foundation`      | —           | ✅ Ferdig    |
| 2    | `feature/normalization`      | 1           | ✅ Ferdig    |
| 3    | `feature/product-persistence`| 1+2         | ✅ Ferdig    |
| 4    | `feature/price-fetch-task`   | 1+2+3       | ✅ Ferdig    |
| 5    | `feature/google-auth`        | 1 + .env    | ✅ Ferdig    |
| 6    | `feature/per-user-isolation` | 5           | ✅ Ferdig    |
| 7    | `feature/shopping-list`      | 1+2+5+6     | ⏳ Neste     |
| 8    | `feature/watchlist`          | 1+2+4+5+6   | 📋 Plan      |
| 9    | `feature/price-history-ui`   | 1+3+4       | 📋 Plan      |
| 10   | `feature/normalization-ui`   | 2+5+6       | 📋 Plan      |
| —    | `fix/search-ux`              | —           | 📋 Plan      |
| —    | `fix/price-baseline`         | —           | 📋 Plan      |
| —    | `fix/price-arrow-semantics`  | —           | 📋 Plan      |
