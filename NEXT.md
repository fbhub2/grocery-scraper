# Neste steg

> Én ting. Gjør denne ferdig før du åpner BACKLOG.md.

---

## ✅ `feature/normalization-ux` merget til dev (mai 2026)

Levert:
- "lettmelk" og "lett melk" gir nå samme søkeresultat
- Kassal-butikker i kombinert søketabell (ikke lenger separat ekspander)
- Normaliserings-UI redesignet: →/⟳-knapper, manuell lagring, ingen tabellhopping
- Auto-normalisering: 30+ compound splits + merkevare-stripping

---

## Nå: STEG 13 — `feature/family-mode`

Delt handleliste på tvers av brukere (familie/husstand).

**Kjernefeatures:**
- `list_member`-tabell: `(list_id, user_id, role)` — owner / member
- Inviter via e-post fra åpen liste
- `get_shopping_lists()` returnerer egne + delte lister
- Visuell markering av delte lister (👥-ikon)

---

## Overordnet veikart

| Steg | Branch                         | Status      |
|------|--------------------------------|-------------|
| 1–11 | (diverse)                      | ✅ Ferdig    |
| —    | `bugfix/search-improvements`   | ✅ Ferdig    |
| —    | `feature/butikk-innstillinger` | ✅ Ferdig    |
| 12   | `feature/single-product-view`  | ✅ Ferdig    |
| —    | `feature/normalization-ux`     | ✅ Ferdig    |
| 13   | `feature/family-mode`          | 📋 Plan      |
