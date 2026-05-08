import httpx
from .base import Product, split_name_variant

_SEARCH_URL = "https://platform-rest-prod.ngdata.no/api/episearch/1300/autosuggest"
_PRODUCT_URL = "https://platform-rest-prod.ngdata.no/api/products/1300/{}"
_STORE_ID = "7080001150488"
_HEADERS = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}


def search(query: str, limit: int = 5) -> list[Product]:
    r = httpx.get(
        _SEARCH_URL,
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

    import db
    store_id = db.ensure_store("meny")

    products = []
    seen_ids: set[str] = set()
    for hit in data.get("products", {}).get("hits", []):
        src = hit.get("contentData", {}).get("_source", {})
        full = f"{src.get('title', '')} {hit.get('description', '')}".strip()
        name, variant = split_name_variant(full)

        ean = str(src.get("ean") or "")
        product_id = ean or str(src.get("productId") or "")
        if product_id and product_id in seen_ids:
            continue
        seen_ids.add(product_id)

        try:
            if product_id:
                db.upsert_product(product_id, name, store_id, ean=ean or None)
            db.upsert_normal(name)
        except Exception:
            pass

        products.append(
            Product(
                name=name,
                price=float(src.get("pricePerUnit", 0)),
                unit_price=f"{src.get('comparePricePerUnit', '')} kr/{src.get('compareUnit', '')}".strip(" kr/") or None,
                url="https://www.meny.no/varer" + src.get("slugifiedUrl", ""),
                variant=variant,
                image_url=(
                    f"https://bilder.ngdata.no/{src['imagePath']}/large.jpg"
                    if src.get("imagePath") else None
                ),
                ean=ean or None,
            )
        )
        if len(products) >= limit:
            break
    return products


async def fetch_price(product_id: str) -> float | None:
    """Hent gjeldende pris for ett produkt fra Meny. Returnerer None ved feil."""
    try:
        async with httpx.AsyncClient(headers=_HEADERS, timeout=10) as client:
            r = await client.get(
                _PRODUCT_URL.format(product_id),
                params={"store_id": _STORE_ID},
            )
            r.raise_for_status()
            data = r.json()
            price = data.get("pricePerUnit")
            return float(price) if price is not None else None
    except Exception:
        return None
