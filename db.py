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
                valid_week   TEXT,
                imported_at  TEXT DEFAULT (datetime('now')),
                valid_updated_at TEXT DEFAULT (datetime('now'))
            );
        """)
        
        # Migration: legg til kolonner hvis de ikke finnes
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(obs_products)")
        columns = {row[1] for row in cursor.fetchall()}
        
        if "valid_week" not in columns:
            conn.execute("ALTER TABLE obs_products ADD COLUMN valid_week TEXT")
        if "valid_updated_at" not in columns:
            conn.execute("ALTER TABLE obs_products ADD COLUMN valid_updated_at TEXT DEFAULT (datetime('now'))")


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


def remove_item(list_name: str, product_name: str) -> None:
    with _conn() as conn:
        conn.execute(
            """DELETE FROM list_items WHERE product_name = ?
               AND list_id = (SELECT id FROM shopping_lists WHERE name = ?)""",
            (product_name, list_name),
        )


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
                valid_from, valid_to, source, image_url, valid_week, valid_updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))""",
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
                    p.get("valid_week"),
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


def get_obs_status() -> dict:
    """
    Hent status for OBS-produkter:
    - total antall
    - gyldig til dato
    - er det utløpt?
    - uke-info
    """
    today = date.today().isoformat()
    with _conn() as conn:
        # Hent alle OBS-produkter (uavhengig av gyldighet)
        rows = conn.execute(
            """SELECT DISTINCT valid_from, valid_to, valid_week
               FROM obs_products ORDER BY valid_to DESC LIMIT 1"""
        ).fetchone()
        
        if not rows:
            return {
                "has_data": False,
                "total_products": 0,
                "valid_from": None,
                "valid_to": None,
                "valid_week": None,
                "is_expired": True,
            }
        
        valid_from = rows["valid_from"]
        valid_to = rows["valid_to"]
        valid_week = rows["valid_week"]
        is_expired = valid_to < today if valid_to else True
        
        # Antall gyldig i dag
        count_active = conn.execute(
            """SELECT COUNT(*) as cnt FROM obs_products
               WHERE valid_to >= ?""",
            (today,),
        ).fetchone()["cnt"]
        
        return {
            "has_data": True,
            "total_products": count_active,
            "valid_from": valid_from,
            "valid_to": valid_to,
            "valid_week": valid_week,
            "is_expired": is_expired,
        }


def clear_expired_obs() -> int:
    """
    Slett OBS-produkter som er utløpt.
    Returnerer antall slettede produkter.
    """
    today = date.today().isoformat()
    with _conn() as conn:
        cursor = conn.execute(
            """DELETE FROM obs_products WHERE valid_to < ?""",
            (today,),
        )
        return cursor.rowcount
