import httpx
from .base import Product

_URL = "https://www.rema.no/api/products"
_HEADERS = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}


def search(query: str, limit: int = 5) -> list[Product]:
    r = httpx.get(
        _URL,
        params={"q": query, "size": limit},
        headers=_HEADERS,
        timeout=10,
    )
    r.raise_for_status()
    data = r.json()

    products = []
    for item in data.get("products", data.get("results", []))[:limit]:
        raw_price = item.get("price", {})
        if isinstance(raw_price, dict):
            price = float(raw_price.get("price", raw_price.get("sales", 0)) or 0)
        else:
            price = float(raw_price or 0)
        products.append(
            Product(
                name=item.get("name", item.get("title", "")),
                price=price,
                unit_price=item.get("unitPrice"),
                url="https://www.rema.no" + item.get("url", ""),
            )
        )
    return products
