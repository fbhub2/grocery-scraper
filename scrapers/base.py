import re
from dataclasses import dataclass, asdict
from typing import Optional

# Matcher størrelsestoken: vekt/volum (1,75 l · 540 g · 330ml) og prosent (0,5% · 1%)
_SIZE_RE = re.compile(
    r'\b\d+[,.]?\d*\s*(?:g|kg|l|ml|dl|cl|stk)\b|\b\d+[,.]?\d*\s*%',
    re.IGNORECASE,
)


def split_name_variant(full: str) -> tuple[str, str | None]:
    """Trekker ut størrelse/variant fra en produktstreng.

    Returnerer (rentnavn, variant) der variant kun inneholder størrelses-tokens
    normalisert til "0,5% · 1,75 l"-format.
    """
    sizes = []
    for m in _SIZE_RE.finditer(full):
        tok = m.group().strip()
        # Sikrer mellomrom mellom tall og bokstavenhet: "1,75l" → "1,75 l"
        tok = re.sub(r'(\d)([a-zA-Z])', r'\1 \2', tok)
        sizes.append(tok)

    name = _SIZE_RE.sub('', full)
    name = re.sub(r'[,\s]+', ' ', name).strip()
    variant = ' · '.join(sizes) if sizes else None
    return name, variant


@dataclass
class Product:
    name: str
    price: float
    unit_price: Optional[str] = None
    url: Optional[str] = None
    variant: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)
