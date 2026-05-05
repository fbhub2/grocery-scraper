import os
import httpx
from .base import Product

_BASE_URL = "https://kassal.app/api/v1"


def _headers() -> dict:
    return {"Authorization": f"Bearer {os.environ.get('KASSAL_API_KEY', '')}"}


def is_configured() -> bool:
    return bool(os.environ.get("KASSAL_API_KEY", "").strip())


def search(query: str, limit: int = 10) -> list[Product]:
    if not is_configured():
        return []
    try:
        r = httpx.get(
            f"{_BASE_URL}/products",
            params={"search": query, "size": min(limit, 100)},
            headers=_headers(),
            timeout=10,
        )
        r.raise_for_status()
    except Exception:
        return []

    products = []
    seen: set[tuple] = set()
    for item in r.json().get("data", []):
        name = item.get("name", "")
        price = item.get("current_price")
        if not name or price is None:
            continue

        store_info = item.get("store") or {}
        store_name = store_info.get("name", "Kassal")
        ean = item.get("ean")

        key = (ean or name.lower(), store_name)
        if key in seen:
            continue
        seen.add(key)

        weight = item.get("weight")
        weight_unit = (item.get("weight_unit") or "").strip()
        variant = f"{weight} {weight_unit}".strip() if weight else None

        unit_price = item.get("current_unit_price")
        unit_price_str = f"{unit_price:.2f} kr/enhet" if unit_price else None

        products.append(Product(
            name=name,
            price=float(price),
            unit_price=unit_price_str,
            url=item.get("url", ""),
            variant=variant,
            image_url=item.get("image"),
            ean=ean,
            store_name=store_name,
        ))
        if len(products) >= limit:
            break
    return products
