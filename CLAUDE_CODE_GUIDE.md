# Claude Code — Rask opplæring for grocery-scraper

## Installasjon (én gang)
```powershell
npm install -g @anthropic-ai/claude-code
```

## Slik bruker du det

### Enkel kommando (én oppgave)
```powershell
cd C:\mittprosjekt
claude "implementer db.py med SQLite-støtte basert på mcp_task.md"
```

### Interaktiv modus (anbefalt for større jobber)
```powershell
cd C:\mittprosjekt
claude
```
Da åpnes en REPL. Du kan gi instrukser, stille oppfølgingsspørsmål og se hva Claude gjør steg for steg.

### Plan først, så implementer
```powershell
claude --plan "implementer alle filene i mcp_task.md"
```
Claude viser plan → du godkjenner → så kjøres den.

---

## Riktig arbeidsflyt for dette prosjektet

**Første gang (bootstrapping):**
```powershell
cd C:\mittprosjekt
claude "/init"         # genererer utkast til CLAUDE.md basert på kodebasen
# Rediger CLAUDE.md etterpå — kopier innholdet fra vår CLAUDE.md
```

**Implementer MCP-støtte (alt i én kommando):**
```powershell
claude "Les mcp_task.md og implementer alle stegene i rekkefølge.
Sjekk faktisk filstruktur først med ls/dir. Ikke anta importstier."
```

**Legg til én ting om gangen:**
```powershell
claude "implementer normalize.py basert på steg 4 i mcp_task.md"
claude "implementer db.py basert på steg 3 i mcp_task.md"
claude "implementer mcp_server.py og tilpass importstiene til faktisk filstruktur"
```

---

## Nyttige kommandoer i Claude Code

| Kommando | Hva den gjør |
|---|---|
| `/init` | Generer CLAUDE.md fra kodebasen |
| `/clear` | Nullstill kontekst (bruk ved 70%+ kontekstfyll) |
| `/compact` | Komprimer kontekst uten å miste alt |
| `/permissions` | Allowlist kommandoer som ikke trenger godkjenning |
| `Shift+Tab` | Bytt til auto-godkjenning (færre klikk) |

---

## Tips for dette prosjektet

1. **Kjør alltid fra `C:\mittprosjekt`** — CLAUDE.md leses automatisk
2. **CLAUDE.md er din huskeliste til Claude** — hold den oppdatert
3. **Del opp store oppgaver** — "implementer db.py" er bedre enn "implementer alt"
4. **Gi Claude feilmeldingen** — lim inn Python-traceback direkte, si "fiks dette"
5. **OBS-import workflow:** `claude "her er bilde av OBS-tilbudsavis, parse og importer via import_obs_catalog"`

---

## Eksempel på OBS-import via Claude Code
```powershell
# I Claude Code interaktiv modus:
claude
> Jeg har et bilde av OBS tilbudsavis. Les bildet på C:\bilder\obs_uke17.jpg,
> ekstrahér alle produkter med pris, og kall import_obs_catalog med
> valid_from=2026-04-21 og valid_to=2026-04-27
```

---

## Eksempel på screenshot → handleliste
```powershell
claude
> Her er et bilde av min Oda-handleliste: C:\bilder\oda_liste.png
> Les alle produkter og legg dem til i handlelisten "ukesliste" via add_multiple_to_list
```
