import re


# ---------------------------------------------------------------------------
# v1.x — beholdes for MCP-server og app.py
# ---------------------------------------------------------------------------

def normalize_search_term(raw: str) -> str:
    """
    Normaliser et søkeord for matching på tvers av butikker.
    Fjerner volum-tokens, gjør lowercase, trimmer whitespace.
    Eksempel: "Tine Lettmelk 1,5 l" -> "tine lettmelk"
    """
    cleaned = re.sub(
        r'\d+[\.,]?\d*\s*(ml|l|g|kg|cl|dl|stk)', '', raw, flags=re.IGNORECASE
    )
    cleaned = re.sub(r'\s+', ' ', cleaned).strip().lower()
    return cleaned


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


# ---------------------------------------------------------------------------
# v2.0 — auto-normalisering
# ---------------------------------------------------------------------------

COMPOUND_SPLITS = {
    "lettmelk":        "lett melk",
    "helmelk":         "hel melk",
    "skummetmelk":     "skummet melk",
    "kremfløte":       "krem fløte",
    "havregryn":       "havre gryn",
    "fullkornbrød":    "fullkorn brød",
    "knekkebrød":      "knekke brød",
    "jordbærsyltetøy": "jordbær syltetøy",
}

_UNIT_ALIASES = {
    "liter": "l",
    "ltr":   "l",
    "gram":  "g",
    "gr":    "g",
    "kilogram": "kg",
}

_UNIT_PATTERN = re.compile(
    r'(\d+[\.,]?\d*)\s*(liter|ltr|kilogram|gram|ml|dl|cl|kg|gr|g|l|stk)',
    re.IGNORECASE,
)


def _normalize_volume_token(m: re.Match) -> str:
    number_str = m.group(1)
    unit = _UNIT_ALIASES.get(m.group(2).lower(), m.group(2).lower())
    try:
        number = float(number_str.replace(',', '.'))
        if unit == 'g' and number >= 1000 and number % 1000 == 0:
            return f"{int(number // 1000)}kg"
    except ValueError:
        pass
    return f"{number_str}{unit}"


def auto_normalize(original_name: str) -> str:
    """
    Normaliser et produktnavn for lagring i normal.auto_name.
    Rekkefølge:
      1. CamelCase-splitting (før lowercase)
      2. Lowercase
      3. Kjente sammensetninger via COMPOUND_SPLITS
      4. Volum/vekt-normalisering: '1L'/'1 liter' → '1l', '1000g' → '1kg'
      5. Kollaps whitespace
    """
    # 1. CamelCase: "TineLettmelk" → "Tine Lettmelk"
    text = re.sub(r'([a-z])([A-Z])', r'\1 \2', original_name)
    # 2. Lowercase
    text = text.lower()
    # 3. Compound splits (hele ord)
    for compound, split in COMPOUND_SPLITS.items():
        text = re.sub(r'\b' + re.escape(compound) + r'\b', split, text)
    # 4. Volum-normalisering
    text = _UNIT_PATTERN.sub(_normalize_volume_token, text)
    # 5. Kollaps whitespace
    return re.sub(r'\s+', ' ', text).strip()


def resolve_name(original_name: str, user_id: int = None) -> str:
    """
    Eneste funksjon UI skal kalle for å vise produktnavn.
    Prioritet: custom_name (user_normal) > auto_name (normal) > original_name.
    """
    import db
    return db.get_display_name(original_name, user_id)


# ---------------------------------------------------------------------------
# v2.0 — terskellogikk for varslingsliste
# ---------------------------------------------------------------------------

def check_threshold(item: dict, current_price: float, avg_price: float) -> bool:
    """
    Returner True hvis current_price treffer terskelen i item.
    item må ha nøklene: threshold_type, threshold_value.
    """
    t = item["threshold_type"]
    if t == "absolute":
        return current_price < item["threshold_value"]
    if t == "relative":
        return current_price < avg_price * (1 - item["threshold_value"] / 100)
    if t == "sale":
        return current_price < avg_price * 0.90
    return False
