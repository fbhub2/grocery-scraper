# Neste steg

> Én ting. Gjør denne ferdig før du åpner BACKLOG.md.

---

## ✅ Nå: Varsling ved prisfall

Gi brukeren beskjed når en vare på handlelisten har falt i pris siden sist søk.

**Branch:** `feature/prisvarsel`

```powershell
git checkout -b feature/prisvarsel
```

**Scope:**
- Bruk eksisterende `get_price_trend()` fra db.py
- Etter "Søk alle på listen": vis `st.success("↓ Prisfall!")` per vare der `trend["delta"] < 0`
- Vis i sidebar under handlelisten: liten badge/caption med "Prisfall siden sist" hvis trend finnes

**Ikke gjør:**
- Ingen e-post eller push-varsler — kun i-app visning
- Ingen ny database-tabell — alt data finnes allerede i price_history

---

*Oppdater denne filen når steget er fullført og du velger neste oppgave fra BACKLOG.md.*
