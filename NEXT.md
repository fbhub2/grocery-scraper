# Neste steg

> Én ting. Gjør denne ferdig før du åpner BACKLOG.md.

---

## ✅ STEG 13 implementert — `feature/family-mode` (mai 2026)

Branch klar for test og merge til dev.

**Test manuelt:**
1. `streamlit run app.py`
2. Gå til Handlelister → åpne en liste du eier
3. Klikk "👥 Del liste" → kopier URL → åpne i nytt vindu med annen bruker
4. Verifiser at listen vises med 👥-ikon hos member, og at eier ser members-lista
5. Test "Forlat liste" som member og "Fjern member" som eier

**Merk:** Del-URL bruker `st.query_params.get("_base_url")` som fallback — i prod
vil base-URL-en ikke settes automatisk. Vurder å hardkode prod-URL som env-variabel
eller la brukeren kopiere fra nettleseren selv.

---

## Nå: STEG 14 eller release til main

**Kandidater:**
- **Release til main** — alle STEG 1–13 er ferdig og testet på dev
- **STEG 14** — OBS-import v2 (automatisk refresh, utløpsdato) + MCP-fix
- **Bugfix** — del-liste base-URL-håndtering for Streamlit Cloud

---

## Overordnet veikart

| Steg | Branch                         | Status      |
|------|--------------------------------|-------------|
| 1–11 | (diverse)                      | ✅ Ferdig    |
| 12   | `feature/single-product-view`  | ✅ Ferdig    |
| —    | `feature/normalization-ux`     | ✅ Ferdig    |
| 13   | `feature/family-mode`          | ⏳ Test      |
| 14   | OBS-import v2 / MCP-fix        | 📋 Plan      |
