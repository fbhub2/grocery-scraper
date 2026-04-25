import re


def parse_product_name(raw_name: str) -> dict:
    """
    Trekk ut strukturerte felt fra råproduktnavn.
    Brukes av compare_prices for å matche på tvers av Oda/Meny/OBS.
    Returnerer: {brand, product_name, volume, unit}
    """
    volume_match = re.search(
        r'(\d+[\.,]?\d*)\s*(ml|l|g|kg|cl|dl|stk)', raw_name, re.IGNORECASE
    )
    volume = volume_match.group(0) if volume_match else None
    clean = re.sub(
        r'\d+[\.,]?\d*\s*(ml|l|g|kg|cl|dl|stk)', '', raw_name, flags=re.IGNORECASE
    ).strip()
    return {
        "raw": raw_name,
        "product_name": clean,
        "volume": volume,
        "brand": None,
        "unit": volume_match.group(2).lower() if volume_match else None,
    }
