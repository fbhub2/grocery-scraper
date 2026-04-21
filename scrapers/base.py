from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class Product:
    name: str
    price: float
    unit_price: Optional[str] = None
    url: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)
