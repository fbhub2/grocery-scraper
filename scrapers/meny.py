import httpx
from .base import Product

_URL = "https://platform-rest-prod.ngdata.no/api/episearch/1300/autosuggest"
_STORE_ID = "7080001150488"
_HEADERS = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}


def search(query: str, limit: int = 5) -> list[Product]:
    r = httpx.get(
        _URL,
        params={
            "types": "suggest,products",
            "search": query,
            "page_size": limit,
            "store_id": _STORE_ID,
            "popularity": "true",
            "showNotForSale": "true",
            "version": "1",
        },
        headers=_HEADERS,
        timeout=10,
    )
    r.raise_for_status()
    data = r.json()

    products = []
    for hit in data.get("products", {}).get("hits", [])[:limit]:
        src = hit.get("contentData", {}).get("_source", {})
        name = src.get("title", hit.get("title", ""))
        desc = hit.get("description", "")
        if desc:
            name = f"{name} {desc}"
        products.append(
            Product(
                name=name,
                price=float(src.get("pricePerUnit", 0)),
                unit_price=f"{src.get('comparePricePerUnit', '')} kr/{src.get('compareUnit', '')}".strip(" kr/") or None,
                url="https://www.meny.no/varer" + src.get("slugifiedUrl", ""),
            )
        )
    return products
