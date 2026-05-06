# Neste steg

> Én ting. Gjør denne ferdig før du åpner BACKLOG.md.

---

## ✅ Vedlikehold utført — mai 2026

- `tasks.py` — `run_auto_normalize(force=True)` overskriv alle auto_name
- `tasks.py` — CLI-flagg `python tasks.py normalize --force`
- `app.py` — admin-knapp "🔄 Kjør auto-normalisering (force)"
- `app.py` — `SHARE_BASE_URL` env-variabel for del-liste-URL
- 95 eksisterende produktnavn kjørt gjennom ny normalize-logikk

---

## Neste: STEG 14 — `feature/obs-import-v2`

**Mål:**
- OBS-tilbudsavis: automatisk refresh via `tasks.py`
- Utløpsdato-håndtering (skjul utgåtte OBS-tilbud)
- **Langsiktig:** Ollama-lokal → MCP → prod-db pipeline

**Forutsetning:**
- Branchen `feature/obs-import` finnes allerede (se git log)
- Sjekk hva som er gjort der før du starter nytt arbeid

---

## Overordnet veikart

| Steg | Branch                         | Status      |
|------|--------------------------------|-------------|
| 1–11 | (diverse)                      | ✅ Ferdig    |
| 12   | `feature/single-product-view`  | ✅ Ferdig    |
| —    | `feature/normalization-ux`     | ✅ Ferdig    |
| 13   | `feature/family-mode`          | ✅ Ferdig    |
| —    | vedlikehold mai 2026           | ✅ Ferdig    |
| 14   | `feature/obs-import-v2`        | 📋 Neste     |
| 15   | Streamlit Cloud deploy         | 📋 Plan      |
