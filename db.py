import sqlite3
from datetime import date
from pathlib import Path

DB_PATH = Path(__file__).parent / "grocery.db"


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _init() -> None:
    with _conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS shopping_lists (
                id         INTEGER PRIMARY KEY,
                name       TEXT UNIQUE NOT NULL,
                created_at TEXT DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS list_items (
                id           INTEGER PRIMARY KEY,
                list_id      INTEGER REFERENCES shopping_lists(id),
                product_name TEXT,
                brand        TEXT,
                volume       TEXT,
                store        TEXT,
                price        REAL,
                image_url    TEXT,
                quantity     INTEGER DEFAULT 1,
                added_at     TEXT DEFAULT (datetime('now')),
                checked      INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS obs_products (
                id           INTEGER PRIMARY KEY,
                product_name TEXT,
                brand        TEXT,
                volume       TEXT,
                price        REAL,
                normal_price REAL,
                valid_from   TEXT,
                valid_to     TEXT,
                source       TEXT,
                image_url    TEXT,
                imported_at  TEXT DEFAULT (datetime('now'))
            );
        """)


_init()


def _ensure_list(conn: sqlite3.Connection, list_name: str) -> int:
    conn.execute("INSERT OR IGNORE INTO shopping_lists (name) VALUES (?)", (list_name,))
    return conn.execute(
        "SELECT id FROM shopping_lists WHERE name = ?", (list_name,)
    ).fetchone()["id"]


def add_item(
    list_name: str,
    product_name: str,
    store: str = None,
    price: float = None,
    quantity: int = 1,
    image_url: str = None,
    brand: str = None,
    volume: str = None,
) -> None:
    with _conn() as conn:
        list_id = _ensure_list(conn, list_name)
        conn.execute(
            """INSERT INTO list_items
               (list_id, product_name, brand, volume, store, price, image_url, quantity)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (list_id, product_name, brand, volume, store, price, image_url, quantity),
        )


def get_list(list_name: str = "default") -> list[dict]:
    with _conn() as conn:
        rows = conn.execute(
            """SELECT li.* FROM list_items li
               JOIN shopping_lists sl ON li.list_id = sl.id
               WHERE sl.name = ? ORDER BY li.added_at""",
            (list_name,),
        ).fetchall()
    return [dict(r) for r in rows]


def get_all_lists() -> list[str]:
    with _conn() as conn:
        rows = conn.execute(
            "SELECT name FROM shopping_lists ORDER BY created_at"
        ).fetchall()
    return [r["name"] for r in rows]


def add_obs_products(products: list[dict]) -> None:
    with _conn() as conn:
        conn.executemany(
            """INSERT INTO obs_products
               (product_name, brand, volume, price, normal_price,
                valid_from, valid_to, source, image_url)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            [
                (
                    p.get("product_name"),
                    p.get("brand"),
                    p.get("volume"),
                    p.get("price"),
                    p.get("normal_price"),
                    p.get("valid_from"),
                    p.get("valid_to"),
                    p.get("source"),
                    p.get("image_url"),
                )
                for p in products
            ],
        )


def search_obs(query: str) -> list[dict]:
    today = date.today().isoformat()
    with _conn() as conn:
        rows = conn.execute(
            """SELECT * FROM obs_products
               WHERE valid_to >= ? AND product_name LIKE ?
               ORDER BY price""",
            (today, f"%{query}%"),
        ).fetchall()
    return [dict(r) for r in rows]
