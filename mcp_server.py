import asyncio
from datetime import date

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types
from rapidfuzz import fuzz

from scrapers.oda import search as oda_search
from scrapers.meny import search as meny_search
from normalize import parse_product_name
import db

app = Server("grocery-scraper")


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="search_products",
            description="Søk etter produkter hos Oda, Meny og OBS (lokal). Returnerer bilde-URL, pris, butikk.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Søkeord"},
                    "limit": {"type": "integer", "default": 5},
                    "category": {
                        "type": "string",
                        "description": "Valgfritt kategorifilter, f.eks. 'melk', 'kjøtt'",
                    },
                },
                "required": ["query"],
            },
        ),
        types.Tool(
            name="compare_prices",
            description="Sammenlign pris på et produkt mellom Oda, Meny og OBS. Normaliserer produktnavn for bedre matching.",
            inputSchema={
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        ),
        types.Tool(
            name="get_store_list",
            description="List støttede butikker",
            inputSchema={"type": "object", "properties": {}},
        ),
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
                    "list_name": {"type": "string", "default": "default"},
                },
                "required": ["product_name"],
            },
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
                                "image_url": {"type": "string"},
                            },
                            "required": ["product_name"],
                        },
                    },
                },
                "required": ["items"],
            },
        ),
        types.Tool(
            name="get_list",
            description="Hent innholdet i en handleliste",
            inputSchema={
                "type": "object",
                "properties": {"list_name": {"type": "string", "default": "default"}},
            },
        ),
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
                                "image_url": {"type": "string"},
                            },
                            "required": ["product_name", "price"],
                        },
                    },
                    "valid_from": {"type": "string", "description": "YYYY-MM-DD"},
                    "valid_to": {"type": "string", "description": "YYYY-MM-DD"},
                    "source_label": {
                        "type": "string",
                        "description": "f.eks. 'tilbudsavis_uke_17_2026'",
                    },
                },
                "required": ["items", "valid_from", "valid_to"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict):

    if name == "get_store_list":
        return [types.TextContent(type="text", text="Oda, Meny, OBS (lokal/tilbudsavis)")]

    if name == "search_products":
        query = arguments["query"]
        limit = arguments.get("limit", 5)
        oda, meny = await asyncio.gather(
            asyncio.to_thread(oda_search, query, limit),
            asyncio.to_thread(meny_search, query, limit),
        )
        obs = db.search_obs(query)
        oda_dicts = [{**p.to_dict(), "store": "Oda"} for p in oda]
        meny_dicts = [{**p.to_dict(), "store": "Meny"} for p in meny]
        obs_dicts = [{**o, "name": o.get("product_name", "")} for o in obs]
        all_results = oda_dicts + meny_dicts + obs_dicts
        scored = sorted(
            all_results,
            key=lambda p: fuzz.token_sort_ratio(query, p.get("name", "")),
            reverse=True,
        )
        return [types.TextContent(type="text", text=str(scored[:limit]))]

    if name == "compare_prices":
        query = arguments["query"]
        oda, meny = await asyncio.gather(
            asyncio.to_thread(oda_search, query, 1),
            asyncio.to_thread(meny_search, query, 1),
        )
        obs = db.search_obs(query)
        results = {}
        if oda:
            d = oda[0].to_dict()
            results["Oda"] = {**d, "normalized": parse_product_name(d.get("name", ""))}
        if meny:
            d = meny[0].to_dict()
            results["Meny"] = {**d, "normalized": parse_product_name(d.get("name", ""))}
        if obs:
            results["OBS"] = {
                **obs[0],
                "normalized": parse_product_name(obs[0].get("product_name", "")),
            }
        return [types.TextContent(type="text", text=str(results))]

    if name == "add_to_list":
        db.add_item(
            list_name=arguments.get("list_name", "default"),
            product_name=arguments["product_name"],
            store=arguments.get("store"),
            price=arguments.get("price"),
            quantity=arguments.get("quantity", 1),
            image_url=arguments.get("image_url"),
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
                image_url=item.get("image_url"),
            )
        count = len(arguments["items"])
        return [types.TextContent(type="text", text=f"Lagt til {count} produkter i '{list_name}'")]

    if name == "get_list":
        items = db.get_list(arguments.get("list_name", "default"))
        return [types.TextContent(type="text", text=str(items))]

    if name == "import_obs_catalog":
        products = [
            {
                **item,
                "valid_from": arguments["valid_from"],
                "valid_to": arguments["valid_to"],
                "source": arguments.get("source_label", f"obs_{date.today()}"),
            }
            for item in arguments["items"]
        ]
        db.add_obs_products(products)
        count = len(products)
        return [
            types.TextContent(
                type="text",
                text=f"Importerte {count} OBS-produkter. Gyldige til {arguments['valid_to']}",
            )
        ]

    return [types.TextContent(type="text", text=f"Ukjent verktøy: {name}")]


async def main() -> None:
    print("Grocery Scraper MCP server running on stdio")
    async with stdio_server() as (r, w):
        await app.run(r, w, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
