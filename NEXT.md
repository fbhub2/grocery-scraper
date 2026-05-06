# Neste steg

> Én ting. Gjør denne ferdig før du åpner BACKLOG.md.

---

## ✅ STEG 12 implementert — `feature/single-product-view` (mai 2026)

Branch klar for test og merge til dev.

**Test manuelt:**
1. `streamlit run app.py`
2. Søk etter et produkt (f.eks. "melk")
3. Klikk én rad i søketabellen → sjekk at "🔍 Vis detaljer →" dukker opp
4. Klikk knappen → produktdetalj-visning med alle butikker + historikk
5. Klikk "← Tilbake til søk" → søkeresultater er bevart

---

## Nå: STEG 13 — `feature/family-mode`

Delt handleliste på tvers av brukere (familie/husstand).

**Kjernefeatures:**
- Inviter andre brukere til en delt liste via e-post
- `list_member`-tabell: `(list_id, user_id, role)` — owner / member
- `get_shopping_lists()` returnerer egne + delte lister
- UI: invite-knapp på åpen liste, visuell markering av delte lister

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
| —    | `feature/butikk-innstillinger` | ✅ Ferdig    |
| 12   | `feature/single-product-view`  | ⏳ Test      |
| 13   | `feature/family-mode`          | 📋 Plan      |
