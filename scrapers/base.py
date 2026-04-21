from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class Product:
    name: str
    price: float
    unit_price: Optional[str] = None
    url: Optional[str] = None
    variant: Optional[str] = None  # størrelse/variant, f.eks. "1,75 l" eller "1% fett, 1,75 l"

    def to_dict(self) -> dict:
        return asdict(self)
