import httpx
from .base import Product, split_name_variant

_URL = "https://oda.com/api/v1/search/mixed/"
_HEADERS = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}


def search(query: str, limit: int = 5) -> list[Product]:
    r = httpx.get(_URL, params={"q": query, "type": "mixed"}, headers=_HEADERS, timeout=10)
    r.raise_for_status()
    data = r.json()

    products = []
    for item in data.get("items", []):
        if item.get("type") != "product":
            continue
        a = item["attributes"]
        unit = f"{a.get('gross_unit_price', '')} kr/{a.get('unit_price_quantity_abbreviation', '')}".strip(" kr/") or None
        products.append(Product(
            name=a["name"],
            price=float(a["gross_price"]),
            unit_price=unit,
            url=a.get("front_url", ""),
            variant=split_name_variant(a.get("name_extra", ""))[1],
        ))
        if len(products) >= limit:
            break
    return products
