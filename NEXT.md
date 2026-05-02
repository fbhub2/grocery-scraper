# Neste steg

> Én ting. Gjør denne ferdig før du åpner BACKLOG.md.

---

## ✅ STEG 4 ferdig — `feature/price-fetch-task` (mai 2026)

126 tester grønne. Merget til main.

## Nå: `feature/google-auth` (STEG 5) — BLOKKERT ⚠️

**Blokkert:** Krever at du setter opp Google Cloud Console manuelt.

### Du må gjøre dette først:
1. Gå til https://console.cloud.google.com
2. Opprett OAuth 2.0 Client ID (Web application)
3. Sett Redirect URI: `http://localhost:8501/oauth/callback`
4. Kopier Client ID og Client Secret
5. Opprett `.env` i `C:\mittprosjekt\` med:
   ```
   GOOGLE_CLIENT_ID=<din client id>
   GOOGLE_CLIENT_SECRET=<din client secret>
   ```
6. Si fra — da implementerer jeg STEG 5.

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
