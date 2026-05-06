import re


# ---------------------------------------------------------------------------
# v1.x — beholdes for MCP-server og app.py
# ---------------------------------------------------------------------------

def normalize_search_term(raw: str) -> str:
    """
    Normaliser et søkeord for matching på tvers av butikker.
    Fjerner volum-tokens, gjør lowercase, slår split-sammensatte ord sammen.
    Eksempel: "Tine Lettmelk 1,5 l" -> "tine lettmelk"
              "Lett melk 0,5%"      -> "lettmelk 0,5%"
    """
    cleaned = re.sub(
        r'\d+[\.,]?\d*\s*(ml|l|g|kg|cl|dl|stk)', '', raw, flags=re.IGNORECASE
    )
    cleaned = re.sub(r'\s+', ' ', cleaned).strip().lower()
    for split_form, compound in _COMPOUND_JOINS.items():
        cleaned = re.sub(r'\b' + re.escape(split_form) + r'\b', compound, cleaned)
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
    # Melk og meieri
    "lettmelk":         "lett melk",
    "helmelk":          "hel melk",
    "skummetmelk":      "skummet melk",
    "kremfløte":        "krem fløte",
    "rømmedressing":    "rømme dressing",
    "cottage cheese":   "cottage cheese",   # ikke compound, men alias-mapping
    "crème fraîche":    "creme fraiche",
    # Brød og korn
    "havregryn":        "havre gryn",
    "fullkornbrød":     "fullkorn brød",
    "knekkebrød":       "knekke brød",
    "grovbrød":         "grov brød",
    "loffskiver":       "loff skiver",
    # Syltetøy og pålegg
    "jordbærsyltetøy":  "jordbær syltetøy",
    "bringebærsyltetøy":"bringebær syltetøy",
    "jordbærjam":       "jordbær jam",
    "leverpostei":      "lever postei",
    # Kjøtt og fisk
    "kjøttdeig":        "kjøtt deig",
    "kyllingfilet":     "kylling filet",
    "laksfilet":        "laks filet",
    "fiskefilet":       "fiske filet",
    # Grønnsaker og frukt
    "gulrotstappe":     "gulrot stappe",
    "potetmos":         "potet mos",
    # Drikke
    "appelsinjuice":    "appelsin juice",
    "eplejuice":        "eple juice",
    "jordbærjuice":     "jordbær juice",
    "mineralvann":      "mineral vann",
    "farrisvann":       "farris vann",
}

# Reverse: join split compounds back to one word — brukes i normalize_search_term
_COMPOUND_JOINS = {v: k for k, v in COMPOUND_SPLITS.items()}

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


# Kjente merkevarer som fjernes fra auto_name for bedre matching på tvers av butikker.
# Kun ord som aldri er produktbeskrivende (ikke f.eks. "Fjordland" som kan være merke OG sted).
_BRAND_WORDS = {
    "tine", "q-meieriene", "q meieriene", "bama", "mills", "stabburet",
    "hansa", "ringnes", "maarud", "sætre", "freia", "nidar", "fazer",
    "orkla", "norvegia", "jarlsberg", "kavli", "lerum", "nora",
    "findus", "eismann", "felix", "vitana", "knorr", "maggi",
}


def auto_normalize(original_name: str) -> str:
    """
    Normaliser et produktnavn for lagring i normal.auto_name.
    Rekkefølge:
      1. CamelCase-splitting (før lowercase)
      2. Lowercase
      3. Kjente sammensetninger via COMPOUND_SPLITS
      4. Volum/vekt-normalisering: '1L'/'1 liter' → '1l', '1000g' → '1kg'
      5. Fjern kjente merkevarer
      6. Kollaps whitespace
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
    # 5. Fjern merkevarer (hele ord, case-insensitive allerede lowercased)
    for brand in _BRAND_WORDS:
        text = re.sub(r'\b' + re.escape(brand) + r'\b', '', text, flags=re.IGNORECASE)
    # 6. Kollaps whitespace og fjern overflødige tegn
    text = re.sub(r'[-–]+', ' ', text)
    return re.sub(r'\s+', ' ', text).strip().strip(',').strip()


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
