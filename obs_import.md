# OBS-PDF Import Guide

## Oversikt
OBS-tilbudsaviser hentes fra https://kundeavis-obs.coop.no/fso/ og parses med Claude vision.
Resultatene importeres til lokal SQLite via `import_obs_catalog` MCP-tool.

## Workflow

### 1. Last ned eller ta screenshot av OBS-kundeavis
- Gå til: https://kundeavis-obs.coop.no/fso/
- Velg butikk (f.eks. Vinterbro)
- Download PDF eller ta screenshot av relevant side

### 2. Parse med Claude vision
Bruk Claude.ai eller claude.ai/code med vision:

**Prompt-template:**
```
Jeg har et bilde/PDF av OBS-kundeavis fra uke [UKE], gyldig [FRA_DATO] til [TIL_DATO].

Ekstrahér alle produkter med:
- Produktnavn (f.eks. "Norvegia 28% fett")
- Merke/brand (hvis synlig)
- Størrelse/volum (f.eks. "500g", "1L")
- Pris (aktuell pris)
- Normal pris (hvis oppgitt)

Returner som JSON-liste (bare gjeldende produkter):
[
  {
    "product_name": "...",
    "brand": "...",
    "volume": "...",
    "price": XX.XX,
    "normal_price": XX.XX (eller null)
  }
]
```

### 3. Import via MCP-tool
Bruk `import_obs_catalog` MCP-tool fra Claude:

**Input:**
```json
{
  "items": [
    {
      "product_name": "Norvegia 28% fett",
      "brand": "Tine",
      "volume": "500g",
      "price": 29.90,
      "normal_price": 39.90,
      "image_url": "https://..."
    }
  ],
  "valid_from": "2026-04-28",
  "valid_to": "2026-05-04",
  "source_label": "obs_uke_18_2026_vinterbro"
}
```

## Alternativ: Lokal parsing (hvis API tilgjengelig)

Hvis du har Claude API-nøkkel, kan du bruke:
```python
from obs_parser import parse_obs_pdf

result = parse_obs_pdf("kundeavis_uke_18.pdf")
# Returnerer: {
#   "items": [...],
#   "valid_from": "...",
#   "valid_to": "..."
# }
```

## Håndtering i app.py / main.py

Etter import kan OBS-produkter søkes via:
```python
from scrapers import search_products
results = search_products("melk")  # Inkluderer OBS-produkter
```

Se `mcp_server.py` for `search_products` tool-implementering.

## Kjente limitasjoner
- OCR-nøyaktighet avhenger av PDF-kvalitet
- Dato-felt må oppgis manuelt (eller hentes fra PDF-metadata)
- Bildenøkler (product_name) må være entydig for fuzzy-matching
