import os
import re
import httpx
import db
from .base import Product, split_name_variant

_BASE_URL = "https://kassal.app/api/v1"

# Matcher vekt/volum-token for enhetspris-beregning
_QTY_RE = re.compile(
    r'([\d]+[,.]?\d*)\s*(g|kg|l|ml|dl|cl|stk)',
    re.IGNORECASE,
)
_UNIT_FACTORS = {
    "g":   ("kg",  1 / 1000),
    "kg":  ("kg",  1),
    "ml":  ("l",   1 / 1000),
    "dl":  ("l",   0.1),
    "cl":  ("l",   0.01),
    "l":   ("l",   1),
    "stk": ("stk", 1),
}


def _calc_unit_price(price: float, variant: str) -> str | None:
    """Beregn enhetspris fra pris og variant-streng (f.eks. '1,3 kg' → '73.06 kr/kg')."""
    if not variant:
        return None
    m = _QTY_RE.search(variant)
    if not m:
        return None
    try:
        qty = float(m.group(1).replace(",", "."))
        unit = m.group(2).lower()
        label, factor = _UNIT_FACTORS.get(unit, (unit, 1))
        per_unit = price / (qty * factor)
        return f"{per_unit:.2f} kr/{label}"
    except (ValueError, ZeroDivisionError):
        return None


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
        raw_name = item.get("name", "")
        price = item.get("current_price")
        if not raw_name or price is None:
            continue

        store_info = item.get("store") or {}
        store_name = store_info.get("name", "Kassal")
        ean = item.get("ean") or None

        key = (ean or raw_name.lower(), store_name)
        if key in seen:
            continue
        seen.add(key)

        # Prøv API-felter først, fall tilbake til navn-parsing
        weight = item.get("weight")
        weight_unit = (item.get("weight_unit") or "").strip()
        if weight and weight_unit:
            variant = f"{weight} {weight_unit}".strip()
            clean_name = raw_name
        else:
            clean_name, variant = split_name_variant(raw_name)

        # Enhetspris: API-verdi foretrukket, ellers beregn fra variant
        api_unit_price = item.get("current_unit_price")
        if api_unit_price:
            unit_price_str = f"{api_unit_price:.2f} kr/enhet"
        else:
            unit_price_str = _calc_unit_price(float(price), variant)

        try:
            store_id = db.ensure_store(store_name)
            product_key = ean or (clean_name or raw_name).lower()
            db.upsert_product(product_key, clean_name or raw_name, store_id, ean=ean)
        except Exception:
            pass

        products.append(Product(
            name=clean_name or raw_name,
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
