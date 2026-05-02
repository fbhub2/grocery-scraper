import httpx
from .base import Product, split_name_variant

_SEARCH_URL = "https://oda.com/api/v1/search/mixed/"
_PRODUCT_URL = "https://oda.com/api/v1/products/{}/"
_HEADERS = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}


def search(query: str, limit: int = 5) -> list[Product]:
    r = httpx.get(_SEARCH_URL, params={"q": query, "type": "mixed"}, headers=_HEADERS, timeout=10)
    r.raise_for_status()
    data = r.json()

    import db
    store_id = db.ensure_store("oda")

    products = []
    for item in data.get("items", []):
        if item.get("type") != "product":
            continue
        a = item["attributes"]
        unit = f"{a.get('gross_unit_price', '')} kr/{a.get('unit_price_quantity_abbreviation', '')}".strip(" kr/") or None
        images = a.get("images") or []
        image_url = None
        if images and isinstance(images[0], dict):
            thumb = images[0].get("thumbnail")
            if isinstance(thumb, dict):
                image_url = thumb.get("url")
            elif isinstance(thumb, str):
                image_url = thumb

        name = a["name"]
        product_id = str(item.get("id", ""))

        try:
            if product_id:
                db.upsert_product(product_id, name, store_id)
            db.upsert_normal(name)
        except Exception:
            pass

        products.append(Product(
            name=name,
            price=float(a["gross_price"]),
            unit_price=unit,
            url=a.get("front_url", ""),
            variant=split_name_variant(a.get("name_extra", ""))[1],
            image_url=image_url,
        ))
        if len(products) >= limit:
            break
    return products


async def fetch_price(product_id: str) -> float | None:
    """Hent gjeldende pris for ett produkt fra Oda. Returnerer None ved feil."""
    try:
        async with httpx.AsyncClient(headers=_HEADERS, timeout=10) as client:
            r = await client.get(_PRODUCT_URL.format(product_id))
            r.raise_for_status()
            data = r.json()
            price = data.get("gross_price")
            return float(price) if price is not None else None
    except Exception:
        return None
