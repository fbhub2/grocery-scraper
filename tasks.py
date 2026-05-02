import asyncio
import sys
from datetime import date
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import db
from normalize import auto_normalize, check_threshold


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


async def _fetch_all_prices(products: list[dict]) -> list[tuple[dict, float | None]]:
    """Henter priser for alle produkter parallelt."""
    from scrapers.oda import fetch_price as oda_fetch
    from scrapers.meny import fetch_price as meny_fetch

    fetchers = {"oda": oda_fetch, "meny": meny_fetch}

    async def _fetch_one(p: dict) -> tuple[dict, float | None]:
        fetch = fetchers.get(p["store_name"])
        if fetch is None:
            return p, None
        price = await fetch(p["product_id"])
        return p, price

    return await asyncio.gather(*[_fetch_one(p) for p in products])


def run_price_fetch() -> dict:
    """
    Henter gjeldende pris for alle produkter i price_fetch-tabellen.
    Lagrer i product_price_history (UNIQUE per product+store+dato hindrer duplikater).
    Sjekker watchlist-terskler og markerer triggede varsler.
    Returnerer {"fetched": N, "errors": N, "triggered": N}.
    """
    products = db.get_all_price_fetch_products()
    if not products:
        print("run_price_fetch: ingen produkter å hente")
        return {"fetched": 0, "errors": 0, "triggered": 0}

    today = date.today().isoformat()
    results = asyncio.run(_fetch_all_prices(products))

    fetched = errors = triggered = 0

    for product, price in results:
        if price is None:
            errors += 1
            continue

        db.save_price(product["id"], product["store_id"], today, price)
        fetched += 1

        avg = db.get_avg_price(product["id"], product["store_id"], days=30)
        if avg is None:
            continue

        for wl_item in db.get_watchlist_by_name(product["original_name"]):
            if check_threshold(wl_item, price, avg):
                db.mark_watchlist_triggered(wl_item["id"], price, product["store_name"])
                triggered += 1

    print(f"run_price_fetch: hentet {fetched} priser, {errors} feil, {triggered} varsler trigget")
    return {"fetched": fetched, "errors": errors, "triggered": triggered}


if __name__ == "__main__":
    if "normalize" in sys.argv:
        run_auto_normalize()
    elif "fetch" in sys.argv:
        run_price_fetch()
    else:
        print("Bruk: python tasks.py normalize | fetch")
