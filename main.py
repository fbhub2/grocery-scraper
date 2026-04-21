import argparse
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

from scrapers import oda_search, meny_search

STORES = {
    "Oda": oda_search,
    "Meny": meny_search,
}


def run_search(query: str, limit: int) -> tuple[dict, dict]:
    results: dict = {}
    errors: dict = {}

    with ThreadPoolExecutor(max_workers=len(STORES)) as executor:
        futures = {executor.submit(fn, query, limit): name for name, fn in STORES.items()}
        for future in as_completed(futures):
            name = futures[future]
            try:
                results[name] = [p.to_dict() for p in future.result()]
            except Exception as e:
                errors[name] = str(e)
                results[name] = []

    return results, errors


def display(query: str, results: dict, errors: dict) -> None:
    print(f'\nResultater for "{query}":\n')
    for store in STORES:
        print("-" * 50)
        print(f"  {store}")
        print("-" * 50)
        if store in errors:
            print(f"  [FEIL] {errors[store]}\n")
            continue
        products = results.get(store, [])
        if not products:
            print("  Ingen resultater.\n")
            continue
        for p in products:
            unit = f"  ({p['unit_price']})" if p.get("unit_price") else ""
            print(f"  {p['name']:<45} kr {p['price']:.2f}{unit}")
        print()


def save(query: str, results: dict, filename: str) -> None:
    output = {
        "query": query,
        "timestamp": datetime.now().isoformat(),
        "results": results,
    }
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"Lagret til {filename}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Søk etter produktpriser hos Oda, Meny og Rema 1000"
    )
    parser.add_argument("query", help='Produktnavn, f.eks. "melk" eller "havregryn"')
    parser.add_argument("-n", "--limit", type=int, default=5, help="Antall treff per butikk (standard: 5)")
    parser.add_argument("-o", "--output", default="resultater.json", help="JSON-outputfil (standard: resultater.json)")
    args = parser.parse_args()

    print(f'Søker etter "{args.query}" ...')
    results, errors = run_search(args.query, args.limit)
    display(args.query, results, errors)
    save(args.query, results, args.output)


if __name__ == "__main__":
    main()
