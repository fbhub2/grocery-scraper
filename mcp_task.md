# mcp_task.md — Implementeringsplan: MCP-støtte i grocery-scraper

## Steg 1: Sjekk faktisk filstruktur
```powershell
cd C:\mittprosjekt
Get-ChildItem -Recurse -Include *.py | Select-Object FullName
cat requirements.txt
```
Bruk resultatet til å justere importstier i mcp_server.py.

## Steg 2: Installer MCP-pakken
```powershell
pip install mcp rapidfuzz
```
Oppdater requirements.txt:
```
httpx>=0.27
streamlit>=1.35
pandas>=2.0
mcp>=1.0
rapidfuzz>=3.0
```

## Steg 3: Opprett db.py (SQLite-lag)
Opprett `db.py` med følgende tabeller og funksjoner:

**Tabeller:**
```sql
shopping_lists (id INTEGER PK, name TEXT, created_at TEXT)
list_items (id INTEGER PK, list_id INTEGER FK, product_name TEXT,
            brand TEXT, volume TEXT, store TEXT, price REAL,
            image_url TEXT, quantity INTEGER DEFAULT 1,
            added_at TEXT, checked INTEGER DEFAULT 0)
obs_products (id INTEGER PK, product_name TEXT, brand TEXT, volume TEXT,
              price REAL, normal_price REAL, valid_from TEXT, valid_to TEXT,
              source TEXT, image_url TEXT, imported_at TEXT)
```

**Funksjoner som må finnes:**
- `add_item(list_name, product_name, store, price, quantity, image_url, brand, volume)`
- `get_list(list_name) -> list[dict]`
- `get_all_lists() -> list[str]`
- `add_obs_products(products: list[dict])`
- `search_obs(query: str) -> list[dict]` — filtrerer på valid_to >= dagens dato

## Steg 4: Opprett normalize.py
Opprett `normalize.py` med:
```python
import re

def parse_product_name(raw_name: str) -> dict:
    """
    Trekk ut strukturerte felt fra råproduktnavn.
    Brukes av compare_prices for å matche på tvers av Oda/Meny/OBS.
    Returnerer: {brand, product_name, volume, unit}
    """
    # Volum-regex: 1L, 500g, 1.5l, 400ml, osv
    volume_match = re.search(r'(\d+[\.,]?\d*)\s*(ml|l|g|kg|cl|dl|stk)', raw_name, re.IGNORECASE)
    volume = volume_match.group(0) if volume_match else None
    # Fjern volum fra navn for renere matching
    clean = re.sub(r'\d+[\.,]?\d*\s*(ml|l|g|kg|cl|dl|stk)', '', raw_name, flags=re.IGNORECASE).strip()
    return {
        "raw": raw_name,
        "product_name": clean,
        "volume": volume,
        "brand": None,  # Utvides med merkeliste eller LLM-kall
        "unit": volume_match.group(2).lower() if volume_match else None
    }
```

## Steg 5: Opprett mcp_server.py
Se mcp_server.py-skjelettet nedenfor. Juster importstiene basert på steg 1.

## Steg 6: Test
```powershell
cd C:\mittprosjekt
python mcp_server.py
```
Forventet output: `Grocery Scraper MCP server running on stdio`

## Steg 7: Verifiser .mcp.json
Filen skal ligge i `C:\mittprosjekt\.mcp.json` og peke på python mcp_server.py.

---

## Fullstendig mcp_server.py skjelett

```python
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types
import asyncio
from datetime import date

# JUSTER DISSE IMPORTENE basert på faktisk filstruktur:
from scrapers.oda import search as oda_search
from scrapers.meny import search as meny_search
from normalize import parse_product_name
from rapidfuzz import fuzz
import db

app = Server("grocery-scraper")

@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        # --- Søk og sammenligning ---
        types.Tool(
            name="search_products",
            description="Søk etter produkter hos Oda, Meny og OBS (lokal). Returnerer bilde-URL, pris, butikk.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Søkeord"},
                    "limit": {"type": "integer", "default": 5},
                    "category": {"type": "string", "description": "Valgfritt kategorifilter, f.eks. 'melk', 'kjøtt'"}
                },
                "required": ["query"]
            }
        ),
        types.Tool(
            name="compare_prices",
            description="Sammenlign pris på et produkt mellom Oda, Meny og OBS. Normaliserer produktnavn for bedre matching.",
            inputSchema={
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"]
            }
        ),
        types.Tool(
            name="get_store_list",
            description="List støttede butikker",
            inputSchema={"type": "object", "properties": {}}
        ),
        # --- Handleliste ---
        types.Tool(
            name="add_to_list",
            description="Legg ett produkt til handlelisten",
            inputSchema={
                "type": "object",
                "properties": {
                    "product_name": {"type": "string"},
                    "store": {"type": "string"},
                    "price": {"type": "number"},
                    "quantity": {"type": "integer", "default": 1},
                    "image_url": {"type": "string"},
                    "list_name": {"type": "string", "default": "default"}
                },
                "required": ["product_name"]
            }
        ),
        types.Tool(
            name="add_multiple_to_list",
            description="Legg til flere produkter på én gang. Brukes ved import fra screenshot/bilde av handleliste.",
            inputSchema={
                "type": "object",
                "properties": {
                    "list_name": {"type": "string", "default": "default"},
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "product_name": {"type": "string"},
                                "quantity": {"type": "number"},
                                "store": {"type": "string"},
                                "price": {"type": "number"},
                                "image_url": {"type": "string"}
                            },
                            "required": ["product_name"]
                        }
                    }
                },
                "required": ["items"]
            }
        ),
        types.Tool(
            name="get_list",
            description="Hent innholdet i en handleliste",
            inputSchema={
                "type": "object",
                "properties": {
                    "list_name": {"type": "string", "default": "default"}
                }
            }
        ),
        # --- OBS import ---
        types.Tool(
            name="import_obs_catalog",
            description="Importer OBS-tilbudsavis. Claude vision parser PDF/bilde, resultat lagres i lokal SQLite.",
            inputSchema={
                "type": "object",
                "properties": {
                    "items": {
                        "type": "array",
                        "description": "Produkter ekstrahert fra bilde/PDF av Claude vision",
                        "items": {
                            "type": "object",
                            "properties": {
                                "product_name": {"type": "string"},
                                "brand": {"type": "string"},
                                "volume": {"type": "string"},
                                "price": {"type": "number"},
                                "normal_price": {"type": "number"},
                                "image_url": {"type": "string"}
                            },
                            "required": ["product_name", "price"]
                        }
                    },
                    "valid_from": {"type": "string", "description": "YYYY-MM-DD"},
                    "valid_to": {"type": "string", "description": "YYYY-MM-DD"},
                    "source_label": {"type": "string", "description": "f.eks. 'tilbudsavis_uke_17_2026'"}
                },
                "required": ["items", "valid_from", "valid_to"]
            }
        ),
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict):

    if name == "get_store_list":
        return [types.TextContent(type="text", text="Oda, Meny, OBS (lokal/tilbudsavis)")]

    if name == "search_products":
        query = arguments["query"]
        limit = arguments.get("limit", 5)
        oda = await asyncio.to_thread(oda_search, query, limit)
        meny = await asyncio.to_thread(meny_search, query, limit)
        obs = db.search_obs(query)
        # Fuzzy-filter
        all_results = oda + meny + obs
        scored = sorted(all_results, key=lambda p: fuzz.token_sort_ratio(query, p.get("name", "")), reverse=True)
        return [types.TextContent(type="text", text=str(scored[:limit]))]

    if name == "compare_prices":
        query = arguments["query"]
        oda = await asyncio.to_thread(oda_search, query, 1)
        meny = await asyncio.to_thread(meny_search, query, 1)
        obs = db.search_obs(query)
        results = {}
        if oda: results["Oda"] = {**oda[0], "normalized": parse_product_name(oda[0].get("name", ""))}
        if meny: results["Meny"] = {**meny[0], "normalized": parse_product_name(meny[0].get("name", ""))}
        if obs: results["OBS"] = {**obs[0], "normalized": parse_product_name(obs[0].get("product_name", ""))}
        return [types.TextContent(type="text", text=str(results))]

    if name == "add_to_list":
        db.add_item(
            list_name=arguments.get("list_name", "default"),
            product_name=arguments["product_name"],
            store=arguments.get("store"),
            price=arguments.get("price"),
            quantity=arguments.get("quantity", 1),
            image_url=arguments.get("image_url")
        )
        return [types.TextContent(type="text", text=f"Lagt til: {arguments['product_name']}")]

    if name == "add_multiple_to_list":
        list_name = arguments.get("list_name", "default")
        for item in arguments["items"]:
            db.add_item(
                list_name=list_name,
                product_name=item["product_name"],
                quantity=item.get("quantity", 1),
                store=item.get("store"),
                price=item.get("price"),
                image_url=item.get("image_url")
            )
        count = len(arguments["items"])
        return [types.TextContent(type="text", text=f"Lagt til {count} produkter i '{list_name}'")]

    if name == "get_list":
        items = db.get_list(arguments.get("list_name", "default"))
        return [types.TextContent(type="text", text=str(items))]

    if name == "import_obs_catalog":
        products = [{
            **item,
            "valid_from": arguments["valid_from"],
            "valid_to": arguments["valid_to"],
            "source": arguments.get("source_label", f"obs_{date.today()}")
        } for item in arguments["items"]]
        db.add_obs_products(products)
        count = len(products)
        return [types.TextContent(type="text", text=f"Importerte {count} OBS-produkter. Gyldige til {arguments['valid_to']}")]

async def main():
    print("Grocery Scraper MCP server running on stdio")
    async with stdio_server() as (r, w):
        await app.run(r, w, app.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
```
