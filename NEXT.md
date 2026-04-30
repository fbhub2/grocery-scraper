# Neste steg

> Én ting. Gjør denne ferdig før du åpner BACKLOG.md.

---

## ✅ Nå: Produktbilde i resultat

Vis `image_url` fra Oda og Meny direkte i Streamlit-appen.

**Branch:** `feature/produktbilde`

```powershell
git checkout -b feature/produktbilde
```

**Scope:**
- Søkeresultater per butikk: vis `st.image(url, width=80)` over produktnavn
- Handleliste i sidebar: vis miniatyrbilde hvis `image_url` er lagret på varen
- `db.add_item()` tar allerede `image_url=` — bare bruk den

**Ikke gjør:**
- Ikke last ned bilder lokalt
- Ikke endre API-kall — `image_url` er allerede i `Product.to_dict()`

---

*Oppdater denne filen når steget er fullført og du velger neste oppgave fra BACKLOG.md.*
