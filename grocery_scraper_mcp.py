import asyncio
from datetime import date
from typing import Optional

from mcp.server.fastmcp import FastMCP
from rapidfuzz import fuzz

from scrapers.oda import search as oda_search
from scrapers.meny import search as meny_search
from normalize import parse_product_name
import db

mcp = FastMCP("grocery-scraper")


@mcp.tool()
def get_store_list() -> str:
    """List støttede butikker"""
    return "Oda, Meny, OBS (lokal/tilbudsavis)"


@mcp.tool()
async def search_products(query: str, limit: int = 5) -> str:
    """Søk etter produkter hos Oda, Meny og OBS. Returnerer navn, pris, butikk og bilde-URL."""
    oda, meny = await asyncio.gather(
        asyncio.to_thread(oda_search, query, limit),
        asyncio.to_thread(meny_search, query, limit),
    )
    obs = db.search_obs(query)
    all_results = (
        [{**p.to_dict(), "store": "Oda"} for p in oda]
        + [{**p.to_dict(), "store": "Meny"} for p in meny]
        + [{**o, "name": o.get("product_name", "")} for o in obs]
    )
    scored = sorted(
        all_results,
        key=lambda p: fuzz.token_sort_ratio(query, p.get("name", "")),
        reverse=True,
    )
    return str(scored[:limit])


@mcp.tool()
async def compare_prices(query: str) -> str:
    """Sammenlign pris på et produkt mellom Oda, Meny og OBS."""
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
    return str(results)


@mcp.tool()
def add_to_list(
    product_name: str,
    list_name: str = "default",
    store: Optional[str] = None,
    price: Optional[float] = None,
    quantity: int = 1,
    image_url: Optional[str] = None,
) -> str:
    """Legg ett produkt til handlelisten"""
    db.add_item(
        list_name=list_name,
        product_name=product_name,
        store=store,
        price=price,
        quantity=quantity,
        image_url=image_url,
    )
    return f"Lagt til: {product_name}"


@mcp.tool()
def add_multiple_to_list(items: list[dict], list_name: str = "default") -> str:
    """Legg til flere produkter på én gang. Brukes ved import fra screenshot/bilde av handleliste."""
    for item in items:
        db.add_item(
            list_name=list_name,
            product_name=item["product_name"],
            quantity=item.get("quantity", 1),
            store=item.get("store"),
            price=item.get("price"),
            image_url=item.get("image_url"),
        )
    return f"Lagt til {len(items)} produkter i '{list_name}'"


@mcp.tool()
def get_list(list_name: str = "default") -> str:
    """Hent innholdet i en handleliste"""
    return str(db.get_list(list_name))


@mcp.tool()
def import_obs_catalog(
    items: list[dict],
    valid_from: str,
    valid_to: str,
    source_label: Optional[str] = None,
) -> str:
    """Importer OBS-tilbudsavis. Claude vision parser PDF/bilde, resultat lagres i lokal SQLite.
    valid_from og valid_to er YYYY-MM-DD."""
    products = [
        {
            **item,
            "valid_from": valid_from,
            "valid_to": valid_to,
            "source": source_label or f"obs_{date.today()}",
        }
        for item in items
    ]
    db.add_obs_products(products)
    return f"Importerte {len(products)} OBS-produkter. Gyldige til {valid_to}"


if __name__ == "__main__":
    mcp.run()
