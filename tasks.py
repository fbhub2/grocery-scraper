import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import db
from normalize import auto_normalize


def run_auto_normalize() -> int:
    """
    Oppdaterer normal.auto_name for alle rader der verdien er NULL.
    Eksisterende auto_name-verdier overskrives aldri.
    Returnerer antall rader oppdatert.
    """
    pending = [r for r in db.list_normals() if r["auto_name"] is None]
    for row in pending:
        db.upsert_normal(row["original_name"], auto_name=auto_normalize(row["original_name"]))
    print(f"auto_normalize: oppdaterte {len(pending)} rader")
    return len(pending)


def run_price_fetch() -> None:
    """Hent priser for alle produkter i price_fetch. Implementeres i STEG 4."""
    print("run_price_fetch: ikke implementert ennå (STEG 4 — feature/price-fetch-task)")


if __name__ == "__main__":
    if "normalize" in sys.argv:
        run_auto_normalize()
    elif "fetch" in sys.argv:
        run_price_fetch()
    else:
        print("Bruk: python tasks.py normalize | fetch")
