import sqlite3
from datetime import date, timedelta
from pathlib import Path

DB_PATH = Path(__file__).parent / "grocery.db"


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _init() -> None:
    with _conn() as conn:
        # --- v1.x tabeller (beholdes for MCP-server og app.py) ---
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
                checked      INTEGER DEFAULT 0,
                search_term  TEXT
            );
            CREATE TABLE IF NOT EXISTS price_history (
                id           INTEGER PRIMARY KEY,
                product_name TEXT NOT NULL,
                store        TEXT NOT NULL,
                price        REAL NOT NULL,
                unit_price   TEXT,
                volume       TEXT,
                recorded_at  TEXT DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS obs_products (
                id               INTEGER PRIMARY KEY,
                product_name     TEXT,
                brand            TEXT,
                volume           TEXT,
                price            REAL,
                normal_price     REAL,
                valid_from       TEXT,
                valid_to         TEXT,
                source           TEXT,
                image_url        TEXT,
                valid_week       TEXT,
                imported_at      TEXT DEFAULT (datetime('now')),
                valid_updated_at TEXT DEFAULT (datetime('now'))
            );

            -- v2.0 tabeller ---
            CREATE TABLE IF NOT EXISTS store (
                id   INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            );
            CREATE TABLE IF NOT EXISTS product (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id    TEXT NOT NULL,
                original_name TEXT NOT NULL,
                store_id      INTEGER NOT NULL REFERENCES store(id),
                UNIQUE(product_id, store_id)
            );
            CREATE TABLE IF NOT EXISTS normal (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                original_name TEXT NOT NULL,
                auto_name     TEXT,
                UNIQUE(original_name)
            );
            CREATE TABLE IF NOT EXISTS user (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                google_sub TEXT NOT NULL UNIQUE,
                email      TEXT NOT NULL,
                name       TEXT,
                created_at TEXT DEFAULT (date('now'))
            );
            CREATE TABLE IF NOT EXISTS user_settings (
                id      INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES user(id),
                key     TEXT NOT NULL,
                value   TEXT NOT NULL,
                UNIQUE(user_id, key)
            );
            CREATE TABLE IF NOT EXISTS user_normal (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL REFERENCES user(id),
                normal_id   INTEGER NOT NULL REFERENCES normal(id),
                custom_name TEXT NOT NULL,
                UNIQUE(user_id, normal_id)
            );
            CREATE TABLE IF NOT EXISTS product_price_history (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL REFERENCES product(id),
                store_id   INTEGER NOT NULL REFERENCES store(id),
                date       TEXT NOT NULL,
                price      REAL NOT NULL,
                UNIQUE(product_id, store_id, date)
            );
            CREATE TABLE IF NOT EXISTS price_fetch (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    INTEGER NOT NULL REFERENCES user(id),
                product_id INTEGER NOT NULL REFERENCES product(id),
                UNIQUE(user_id, product_id)
            );
            CREATE TABLE IF NOT EXISTS shopping_list (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    INTEGER NOT NULL REFERENCES user(id),
                name       TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now')),
                archived   INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS shopping_list_item (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                list_id       INTEGER NOT NULL REFERENCES shopping_list(id),
                original_name TEXT NOT NULL,
                quantity      INTEGER DEFAULT 1,
                note          TEXT,
                checked       INTEGER DEFAULT 0,
                added_at      TEXT DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS watchlist (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id         INTEGER NOT NULL REFERENCES user(id),
                original_name   TEXT NOT NULL,
                threshold_type  TEXT NOT NULL,
                threshold_value REAL,
                status          TEXT DEFAULT 'waiting',
                triggered_at    TEXT,
                triggered_price REAL,
                triggered_store TEXT,
                created_at      TEXT DEFAULT (datetime('now')),
                UNIQUE(user_id, original_name)
            );
            CREATE TABLE IF NOT EXISTS list_member (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                list_id  INTEGER NOT NULL REFERENCES shopping_list(id) ON DELETE CASCADE,
                user_id  INTEGER NOT NULL REFERENCES user(id) ON DELETE CASCADE,
                role     TEXT NOT NULL DEFAULT 'member' CHECK(role IN ('owner','member')),
                added_at TEXT DEFAULT (datetime('now')),
                UNIQUE(list_id, user_id)
            );
            CREATE TABLE IF NOT EXISTS search_history (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL REFERENCES user(id),
                query       TEXT NOT NULL,
                searched_at TEXT DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS session (
                token      TEXT PRIMARY KEY,
                user_json  TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS family (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                name        TEXT NOT NULL,
                invite_code TEXT NOT NULL UNIQUE,
                owner_id    INTEGER NOT NULL REFERENCES user(id),
                created_at  TEXT DEFAULT (date('now'))
            );
            CREATE TABLE IF NOT EXISTS family_member (
                family_id INTEGER NOT NULL REFERENCES family(id) ON DELETE CASCADE,
                user_id   INTEGER NOT NULL REFERENCES user(id) ON DELETE CASCADE,
                role      TEXT NOT NULL DEFAULT 'member' CHECK(role IN ('owner','member')),
                joined_at TEXT DEFAULT (date('now')),
                PRIMARY KEY (family_id, user_id)
            );
        """)

        # v1.x migrasjoner
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(obs_products)")
        obs_cols = {row[1] for row in cursor.fetchall()}
        if "valid_week" not in obs_cols:
            conn.execute("ALTER TABLE obs_products ADD COLUMN valid_week TEXT")
        if "valid_updated_at" not in obs_cols:
            conn.execute("ALTER TABLE obs_products ADD COLUMN valid_updated_at TEXT DEFAULT (datetime('now'))")
        cursor.execute("PRAGMA table_info(list_items)")
        item_cols = {row[1] for row in cursor.fetchall()}
        if "search_term" not in item_cols:
            conn.execute("ALTER TABLE list_items ADD COLUMN search_term TEXT")
        cursor.execute("PRAGMA table_info(price_history)")
        ph_cols = {row[1] for row in cursor.fetchall()}
        if "ean" not in ph_cols:
            conn.execute("ALTER TABLE price_history ADD COLUMN ean TEXT")
        cursor.execute("PRAGMA table_info(shopping_list)")
        sl_cols = {row[1] for row in cursor.fetchall()}
        if "share_token" not in sl_cols:
            conn.execute("ALTER TABLE shopping_list ADD COLUMN share_token TEXT")
            conn.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_sl_share_token "
                "ON shopping_list(share_token) WHERE share_token IS NOT NULL"
            )
        cursor.execute("PRAGMA table_info(product)")
        prod_cols = {row[1] for row in cursor.fetchall()}
        if "ean" not in prod_cols:
            conn.execute("ALTER TABLE product ADD COLUMN ean TEXT")
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_product_ean "
                "ON product(ean) WHERE ean IS NOT NULL"
            )


_init()


# ---------------------------------------------------------------------------
# Intern hjelper
# ---------------------------------------------------------------------------

def _ensure_list(conn: sqlite3.Connection, list_name: str) -> int:
    conn.execute("INSERT OR IGNORE INTO shopping_lists (name) VALUES (?)", (list_name,))
    return conn.execute(
        "SELECT id FROM shopping_lists WHERE name = ?", (list_name,)
    ).fetchone()["id"]


# ---------------------------------------------------------------------------
# v1.x — handleliste (bevares for MCP-server og app.py)
# ---------------------------------------------------------------------------

def add_item(
    list_name: str,
    product_name: str,
    store: str = None,
    price: float = None,
    quantity: int = 1,
    image_url: str = None,
    brand: str = None,
    volume: str = None,
    search_term: str = None,
) -> None:
    with _conn() as conn:
        list_id = _ensure_list(conn, list_name)
        conn.execute(
            """INSERT INTO list_items
               (list_id, product_name, brand, volume, store, price, image_url, quantity, search_term)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (list_id, product_name, brand, volume, store, price, image_url, quantity, search_term),
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


def remove_item(list_name: str, product_name: str, item_id: int = None) -> None:
    with _conn() as conn:
        if item_id is not None:
            conn.execute(
                """DELETE FROM list_items WHERE id = ?
                   AND list_id = (SELECT id FROM shopping_lists WHERE name = ?)""",
                (item_id, list_name),
            )
        else:
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


# ---------------------------------------------------------------------------
# v1.x — prishistorikk (bevares for MCP-server og app.py)
# ---------------------------------------------------------------------------

def record_price(
    product_name: str,
    store: str,
    price: float,
    unit_price: str = None,
    volume: str = None,
    ean: str = None,
) -> None:
    with _conn() as conn:
        conn.execute(
            """INSERT INTO price_history (product_name, store, price, unit_price, volume, ean)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (product_name, store, price, unit_price, volume, ean),
        )


def get_price_history(product_name: str, store: str = None, days: int = 90) -> list[dict]:
    cutoff = (date.today() - timedelta(days=days)).isoformat()
    with _conn() as conn:
        if store:
            rows = conn.execute(
                """SELECT store, price, unit_price, recorded_at FROM price_history
                   WHERE product_name = ? AND store = ? AND recorded_at >= ?
                   ORDER BY recorded_at""",
                (product_name, store, cutoff),
            ).fetchall()
        else:
            rows = conn.execute(
                """SELECT store, price, unit_price, recorded_at FROM price_history
                   WHERE product_name = ? AND recorded_at >= ?
                   ORDER BY recorded_at""",
                (product_name, cutoff),
            ).fetchall()
    return [dict(r) for r in rows]


def get_avg_price_by_name(product_name: str, store: str, days: int = 30) -> float | None:
    rows = get_price_history(product_name, store, days=days)
    if not rows:
        return None
    return sum(r["price"] for r in rows) / len(rows)


def get_market_avg(product_name: str, days: int = 30) -> float | None:
    """Gjennomsnittpris på tvers av alle butikker de siste N dagene."""
    cutoff = (date.today() - timedelta(days=days)).isoformat()
    with _conn() as conn:
        row = conn.execute(
            """SELECT AVG(price) as avg FROM price_history
               WHERE product_name = ? AND recorded_at >= ?""",
            (product_name, cutoff),
        ).fetchone()
    return row["avg"] if row and row["avg"] is not None else None


def get_price_trend(product_name: str, store: str, volume: str = None) -> dict | None:
    with _conn() as conn:
        if volume:
            rows = conn.execute(
                """SELECT price FROM price_history
                   WHERE product_name = ? AND store = ? AND volume = ?
                   ORDER BY id DESC LIMIT 2""",
                (product_name, store, volume),
            ).fetchall()
        else:
            rows = conn.execute(
                """SELECT price FROM price_history
                   WHERE product_name = ? AND store = ?
                   ORDER BY id DESC LIMIT 2""",
                (product_name, store),
            ).fetchall()
    if len(rows) < 2:
        return None
    current, previous = rows[0]["price"], rows[1]["price"]
    delta = current - previous
    pct = (delta / previous * 100) if previous else 0
    return {"current": current, "previous": previous, "delta": delta, "pct": pct}


# ---------------------------------------------------------------------------
# v1.x — OBS-produkter (bevares for MCP-server og app.py)
# ---------------------------------------------------------------------------

def add_obs_products(products: list[dict]) -> None:
    with _conn() as conn:
        conn.executemany(
            """INSERT INTO obs_products
               (product_name, brand, volume, price, normal_price,
                valid_from, valid_to, source, image_url, valid_week, valid_updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))""",
            [
                (
                    p.get("product_name"), p.get("brand"), p.get("volume"),
                    p.get("price"), p.get("normal_price"), p.get("valid_from"),
                    p.get("valid_to"), p.get("source"), p.get("image_url"),
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
    today = date.today().isoformat()
    with _conn() as conn:
        row = conn.execute(
            "SELECT DISTINCT valid_from, valid_to, valid_week FROM obs_products ORDER BY valid_to DESC LIMIT 1"
        ).fetchone()
        if not row:
            return {"has_data": False, "total_products": 0, "valid_from": None,
                    "valid_to": None, "valid_week": None, "is_expired": True}
        count = conn.execute(
            "SELECT COUNT(*) as cnt FROM obs_products WHERE valid_to >= ?", (today,)
        ).fetchone()["cnt"]
    return {
        "has_data": True, "total_products": count,
        "valid_from": row["valid_from"], "valid_to": row["valid_to"],
        "valid_week": row["valid_week"],
        "is_expired": (row["valid_to"] < today) if row["valid_to"] else True,
    }


def clear_expired_obs() -> int:
    today = date.today().isoformat()
    with _conn() as conn:
        cursor = conn.execute("DELETE FROM obs_products WHERE valid_to < ?", (today,))
        return cursor.rowcount


# ---------------------------------------------------------------------------
# v2.0 — butikker og produktkatalog
# ---------------------------------------------------------------------------

def ensure_store(name: str) -> int:
    with _conn() as conn:
        conn.execute("INSERT OR IGNORE INTO store (name) VALUES (?)", (name,))
        return conn.execute("SELECT id FROM store WHERE name = ?", (name,)).fetchone()["id"]


def upsert_product(product_id: str, original_name: str, store_id: int, ean: str = None) -> int:
    ean = ean or None
    with _conn() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO product (product_id, original_name, store_id, ean) VALUES (?, ?, ?, ?)",
            (product_id, original_name, store_id, ean),
        )
        if ean:
            conn.execute(
                "UPDATE product SET ean = ? WHERE product_id = ? AND store_id = ? AND ean IS NULL",
                (ean, product_id, store_id),
            )
        return conn.execute(
            "SELECT id FROM product WHERE product_id = ? AND store_id = ?",
            (product_id, store_id),
        ).fetchone()["id"]


def get_products_by_ean(ean: str) -> list[dict]:
    """Alle butikker som har et produkt med denne EAN."""
    with _conn() as conn:
        rows = conn.execute(
            """SELECT p.id, p.product_id, p.original_name, p.ean, s.name as store_name
               FROM product p JOIN store s ON p.store_id = s.id
               WHERE p.ean = ?""",
            (ean,),
        ).fetchall()
    return [dict(r) for r in rows]


def compare_by_ean(ean: str) -> list[dict]:
    """Kryssbutikk-sammenligning for én EAN: siste pris per butikk."""
    with _conn() as conn:
        rows = conn.execute(
            """SELECT s.name as store_name, p.original_name, p.product_id,
                      pph.price, pph.date
               FROM product p
               JOIN store s ON p.store_id = s.id
               LEFT JOIN product_price_history pph ON pph.product_id = p.id
               WHERE p.ean = ?
               AND (pph.date = (
                   SELECT MAX(h2.date) FROM product_price_history h2
                   WHERE h2.product_id = p.id
               ) OR pph.date IS NULL)
               ORDER BY pph.price ASC NULLS LAST""",
            (ean,),
        ).fetchall()
    return [dict(r) for r in rows]


def get_products(store_id: int = None) -> list[dict]:
    with _conn() as conn:
        if store_id:
            rows = conn.execute(
                "SELECT p.*, s.name as store_name FROM product p JOIN store s ON p.store_id = s.id WHERE p.store_id = ?",
                (store_id,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT p.*, s.name as store_name FROM product p JOIN store s ON p.store_id = s.id"
            ).fetchall()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# v2.0 — normalisering
# ---------------------------------------------------------------------------

def upsert_normal(original_name: str, auto_name: str = None) -> int:
    with _conn() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO normal (original_name, auto_name) VALUES (?, ?)",
            (original_name, auto_name),
        )
        if auto_name is not None:
            conn.execute(
                "UPDATE normal SET auto_name = ? WHERE original_name = ? AND auto_name IS NULL",
                (auto_name, original_name),
            )
        return conn.execute(
            "SELECT id FROM normal WHERE original_name = ?", (original_name,)
        ).fetchone()["id"]


def get_normal_id(original_name: str) -> int | None:
    with _conn() as conn:
        row = conn.execute(
            "SELECT id FROM normal WHERE original_name = ?", (original_name,)
        ).fetchone()
    return row["id"] if row else None


def get_display_name(original_name: str, user_id: int = None) -> str:
    with _conn() as conn:
        if user_id is not None:
            row = conn.execute(
                """SELECT un.custom_name FROM user_normal un
                   JOIN normal n ON un.normal_id = n.id
                   WHERE n.original_name = ? AND un.user_id = ?""",
                (original_name, user_id),
            ).fetchone()
            if row:
                return row["custom_name"]
        row = conn.execute(
            "SELECT auto_name FROM normal WHERE original_name = ?", (original_name,)
        ).fetchone()
        if row and row["auto_name"]:
            return row["auto_name"]
    return original_name


def list_normals_with_custom(user_id: int, filter: str = None) -> list[dict]:
    with _conn() as conn:
        sql = """
            SELECT n.id, n.original_name, n.auto_name, un.custom_name
            FROM normal n
            LEFT JOIN user_normal un ON un.normal_id = n.id AND un.user_id = ?
            {}
            ORDER BY n.original_name
        """.format("WHERE n.original_name LIKE ?" if filter else "")
        params = (user_id, f"%{filter}%") if filter else (user_id,)
        rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


def list_normals(filter: str = None) -> list[dict]:
    with _conn() as conn:
        if filter:
            rows = conn.execute(
                "SELECT * FROM normal WHERE original_name LIKE ? ORDER BY original_name",
                (f"%{filter}%",),
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM normal ORDER BY original_name").fetchall()
    return [dict(r) for r in rows]


def set_custom_name(original_name: str, custom_name: str, user_id: int) -> None:
    normal_id = get_normal_id(original_name)
    if normal_id is None:
        normal_id = upsert_normal(original_name)
    set_custom_name_by_id(normal_id, custom_name, user_id)


def set_custom_name_by_id(normal_id: int, custom_name: str, user_id: int) -> None:
    with _conn() as conn:
        if custom_name:
            conn.execute(
                """INSERT INTO user_normal (user_id, normal_id, custom_name)
                   VALUES (?, ?, ?)
                   ON CONFLICT(user_id, normal_id) DO UPDATE SET custom_name = excluded.custom_name""",
                (user_id, normal_id, custom_name),
            )
        else:
            conn.execute(
                "DELETE FROM user_normal WHERE user_id = ? AND normal_id = ?",
                (user_id, normal_id),
            )


# ---------------------------------------------------------------------------
# v2.0 — brukere
# ---------------------------------------------------------------------------

def ensure_user(google_sub: str, email: str, name: str) -> int:
    with _conn() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO user (google_sub, email, name) VALUES (?, ?, ?)",
            (google_sub, email, name),
        )
        return conn.execute(
            "SELECT id FROM user WHERE google_sub = ?", (google_sub,)
        ).fetchone()["id"]


def get_user_id(google_sub: str) -> int | None:
    with _conn() as conn:
        row = conn.execute(
            "SELECT id FROM user WHERE google_sub = ?", (google_sub,)
        ).fetchone()
    return row["id"] if row else None


def get_user_setting(user_id: int, key: str, default: str = "") -> str:
    with _conn() as conn:
        row = conn.execute(
            "SELECT value FROM user_settings WHERE user_id = ? AND key = ?",
            (user_id, key),
        ).fetchone()
    return row["value"] if row else default


def set_user_setting(user_id: int, key: str, value: str) -> None:
    with _conn() as conn:
        conn.execute(
            """INSERT INTO user_settings (user_id, key, value) VALUES (?, ?, ?)
               ON CONFLICT(user_id, key) DO UPDATE SET value = excluded.value""",
            (user_id, key, str(value)),
        )


# ---------------------------------------------------------------------------
# v2.0 — prishistorikk (product_price_history, global)
# ---------------------------------------------------------------------------

def save_price(product_id: int, store_id: int, price_date: str, price: float) -> None:
    with _conn() as conn:
        conn.execute(
            """INSERT OR IGNORE INTO product_price_history (product_id, store_id, date, price)
               VALUES (?, ?, ?, ?)""",
            (product_id, store_id, price_date, price),
        )


def get_price_history_v2(product_id: int) -> list[dict]:
    with _conn() as conn:
        rows = conn.execute(
            """SELECT pph.date, pph.price, s.name as store
               FROM product_price_history pph
               JOIN store s ON pph.store_id = s.id
               WHERE pph.product_id = ?
               ORDER BY pph.date""",
            (product_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def get_avg_price(product_id: int, store_id: int, days: int = 30) -> float | None:
    cutoff = (date.today() - timedelta(days=days)).isoformat()
    with _conn() as conn:
        row = conn.execute(
            """SELECT AVG(price) as avg FROM product_price_history
               WHERE product_id = ? AND store_id = ? AND date >= ?""",
            (product_id, store_id, cutoff),
        ).fetchone()
    return row["avg"] if row and row["avg"] is not None else None


# ---------------------------------------------------------------------------
# v2.0 — price_fetch (prisovervåkning per bruker)
# ---------------------------------------------------------------------------

def add_to_price_fetch(product_id: int, user_id: int) -> None:
    with _conn() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO price_fetch (user_id, product_id) VALUES (?, ?)",
            (user_id, product_id),
        )


def remove_from_price_fetch(product_id: int, user_id: int) -> None:
    with _conn() as conn:
        conn.execute(
            "DELETE FROM price_fetch WHERE user_id = ? AND product_id = ?",
            (user_id, product_id),
        )


def get_price_fetch_products(user_id: int) -> list[dict]:
    with _conn() as conn:
        rows = conn.execute(
            """SELECT p.*, s.name as store_name FROM price_fetch pf
               JOIN product p ON pf.product_id = p.id
               JOIN store s ON p.store_id = s.id
               WHERE pf.user_id = ?""",
            (user_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def get_all_price_fetch_products() -> list[dict]:
    """Returnerer alle unike produkter i price_fetch på tvers av brukere."""
    with _conn() as conn:
        rows = conn.execute(
            """SELECT DISTINCT p.id, p.product_id, p.original_name, p.store_id,
                      s.name as store_name
               FROM price_fetch pf
               JOIN product p ON pf.product_id = p.id
               JOIN store s ON p.store_id = s.id""",
        ).fetchall()
    return [dict(r) for r in rows]


def get_watchlist_by_name(original_name: str) -> list[dict]:
    """Alle watchlist-items (alle brukere) med gitt original_name og status 'waiting'."""
    with _conn() as conn:
        rows = conn.execute(
            "SELECT * FROM watchlist WHERE original_name = ? AND status = 'waiting'",
            (original_name,),
        ).fetchall()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# v2.0 — handleliste (shopping_list, per bruker)
# ---------------------------------------------------------------------------

def create_shopping_list(user_id: int, name: str) -> int:
    with _conn() as conn:
        cursor = conn.execute(
            "INSERT INTO shopping_list (user_id, name) VALUES (?, ?)", (user_id, name)
        )
        return cursor.lastrowid


def get_shopping_lists(user_id: int) -> list[dict]:
    """Returnerer egne lister + individuelt delte lister + lister fra familie-medlemmer."""
    with _conn() as conn:
        family_rows = conn.execute(
            """SELECT DISTINCT fm2.user_id, f.name as family_name
               FROM family_member fm1
               JOIN family_member fm2 ON fm1.family_id = fm2.family_id
               JOIN family f ON fm1.family_id = f.id
               WHERE fm1.user_id = ? AND fm2.user_id != ?""",
            (user_id, user_id),
        ).fetchall()
        family_user_map = {r["user_id"]: r["family_name"] for r in family_rows}
        family_user_ids = list(family_user_map.keys())

        in_clause = f"({','.join('?' * len(family_user_ids))})" if family_user_ids else "(NULL)"
        rows = conn.execute(
            f"""SELECT sl.*, COUNT(sli.id) as item_count,
                       CASE WHEN sl.user_id = ? THEN 'owner'
                            WHEN sl.id IN (SELECT list_id FROM list_member WHERE user_id = ?) THEN 'member'
                            ELSE 'family' END as my_role,
                       owner.name as owner_name
               FROM shopping_list sl
               LEFT JOIN shopping_list_item sli ON sl.id = sli.list_id
               LEFT JOIN user owner ON sl.user_id = owner.id
               WHERE sl.archived = 0
                 AND (sl.user_id = ?
                      OR sl.id IN (SELECT list_id FROM list_member WHERE user_id = ?)
                      OR sl.user_id IN {in_clause})
               GROUP BY sl.id ORDER BY sl.created_at DESC""",
            (user_id, user_id, user_id, user_id, *family_user_ids),
        ).fetchall()

    result = [dict(r) for r in rows]
    for r in result:
        r["family_name"] = family_user_map.get(r["user_id"]) if r["my_role"] == "family" else None
    return result


def is_list_owner(list_id: int, user_id: int) -> bool:
    with _conn() as conn:
        row = conn.execute(
            "SELECT id FROM shopping_list WHERE id = ? AND user_id = ?", (list_id, user_id)
        ).fetchone()
    return row is not None


def get_list_members(list_id: int) -> list[dict]:
    with _conn() as conn:
        rows = conn.execute(
            """SELECT lm.role, lm.added_at, u.id as user_id, u.email, u.name
               FROM list_member lm JOIN user u ON lm.user_id = u.id
               WHERE lm.list_id = ? ORDER BY lm.added_at""",
            (list_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def add_list_member(list_id: int, user_id: int, role: str = "member") -> None:
    with _conn() as conn:
        conn.execute(
            """INSERT OR IGNORE INTO list_member (list_id, user_id, role) VALUES (?, ?, ?)""",
            (list_id, user_id, role),
        )


def remove_list_member(list_id: int, user_id: int) -> None:
    with _conn() as conn:
        conn.execute(
            "DELETE FROM list_member WHERE list_id = ? AND user_id = ?", (list_id, user_id)
        )


def get_user_by_email(email: str) -> dict | None:
    with _conn() as conn:
        row = conn.execute(
            "SELECT id, email, name FROM user WHERE email = ?", (email.strip().lower(),)
        ).fetchone()
    return dict(row) if row else None


def get_or_create_share_token(list_id: int) -> str:
    import secrets as _secrets
    with _conn() as conn:
        row = conn.execute(
            "SELECT share_token FROM shopping_list WHERE id = ?", (list_id,)
        ).fetchone()
        if row and row["share_token"]:
            return row["share_token"]
        token = _secrets.token_urlsafe(12)
        conn.execute(
            "UPDATE shopping_list SET share_token = ? WHERE id = ?", (token, list_id)
        )
    return token


def get_list_by_share_token(token: str) -> dict | None:
    with _conn() as conn:
        row = conn.execute(
            "SELECT * FROM shopping_list WHERE share_token = ? AND archived = 0", (token,)
        ).fetchone()
    return dict(row) if row else None


def get_shopping_list_items(list_id: int) -> list[dict]:
    with _conn() as conn:
        rows = conn.execute(
            "SELECT * FROM shopping_list_item WHERE list_id = ? ORDER BY added_at",
            (list_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def add_to_shopping_list(
    list_id: int, original_name: str, quantity: int = 1, note: str = None
) -> int:
    with _conn() as conn:
        cursor = conn.execute(
            """INSERT INTO shopping_list_item (list_id, original_name, quantity, note)
               VALUES (?, ?, ?, ?)""",
            (list_id, original_name, quantity, note),
        )
        return cursor.lastrowid


def toggle_item_checked(item_id: int) -> None:
    with _conn() as conn:
        conn.execute(
            "UPDATE shopping_list_item SET checked = NOT checked WHERE id = ?", (item_id,)
        )


def delete_shopping_list(list_id: int) -> None:
    with _conn() as conn:
        conn.execute("DELETE FROM shopping_list_item WHERE list_id = ?", (list_id,))
        conn.execute("DELETE FROM shopping_list WHERE id = ?", (list_id,))


def archive_shopping_list(list_id: int) -> None:
    with _conn() as conn:
        conn.execute(
            "UPDATE shopping_list SET archived = 1 WHERE id = ?", (list_id,)
        )


def remove_shopping_list_item(item_id: int) -> None:
    with _conn() as conn:
        conn.execute("DELETE FROM shopping_list_item WHERE id = ?", (item_id,))


def get_products_with_history() -> list[str]:
    """Unike produktnavn som har prishistorikk, sortert alfabetisk."""
    with _conn() as conn:
        rows = conn.execute(
            "SELECT DISTINCT product_name FROM price_history ORDER BY product_name"
        ).fetchall()
    return [r["product_name"] for r in rows]


# ---------------------------------------------------------------------------
# v2.0 — varslingsliste (watchlist, per bruker)
# ---------------------------------------------------------------------------

def add_to_watchlist(
    user_id: int,
    original_name: str,
    threshold_type: str,
    threshold_value: float = None,
) -> int:
    with _conn() as conn:
        cursor = conn.execute(
            """INSERT INTO watchlist (user_id, original_name, threshold_type, threshold_value)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(user_id, original_name) DO UPDATE SET
                 threshold_type = excluded.threshold_type,
                 threshold_value = excluded.threshold_value,
                 status = 'waiting'""",
            (user_id, original_name, threshold_type, threshold_value),
        )
        return cursor.lastrowid


def remove_from_watchlist(user_id: int, original_name: str) -> None:
    with _conn() as conn:
        conn.execute(
            "DELETE FROM watchlist WHERE user_id = ? AND original_name = ?",
            (user_id, original_name),
        )


def get_watchlist(user_id: int) -> list[dict]:
    with _conn() as conn:
        rows = conn.execute(
            "SELECT * FROM watchlist WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def get_all_watchlist_items() -> list[dict]:
    with _conn() as conn:
        rows = conn.execute("SELECT * FROM watchlist WHERE status = 'waiting'").fetchall()
    return [dict(r) for r in rows]


def mark_watchlist_triggered(watchlist_id: int, price: float, store: str) -> None:
    with _conn() as conn:
        conn.execute(
            """UPDATE watchlist SET status = 'triggered', triggered_at = datetime('now'),
               triggered_price = ?, triggered_store = ? WHERE id = ?""",
            (price, store, watchlist_id),
        )


def reset_watchlist_item(watchlist_id: int) -> None:
    with _conn() as conn:
        conn.execute(
            "UPDATE watchlist SET status = 'waiting', triggered_at = NULL, "
            "triggered_price = NULL, triggered_store = NULL WHERE id = ?",
            (watchlist_id,),
        )


def is_on_watchlist(user_id: int, original_name: str) -> bool:
    with _conn() as conn:
        row = conn.execute(
            "SELECT 1 FROM watchlist WHERE user_id = ? AND original_name = ?",
            (user_id, original_name),
        ).fetchone()
    return row is not None


# ---------------------------------------------------------------------------
# v2.0 — sessions (persistent innlogging på tvers av F5)
# ---------------------------------------------------------------------------

def create_session(token: str, user: dict) -> None:
    import json
    with _conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO session (token, user_json) VALUES (?, ?)",
            (token, json.dumps(user)),
        )


def get_session_user(token: str) -> dict | None:
    import json
    with _conn() as conn:
        row = conn.execute(
            "SELECT user_json FROM session WHERE token = ?", (token,)
        ).fetchone()
    return json.loads(row["user_json"]) if row else None


def delete_session(token: str) -> None:
    with _conn() as conn:
        conn.execute("DELETE FROM session WHERE token = ?", (token,))


# ---------------------------------------------------------------------------
# v2.0 — familie (delt tilgang til alle lister på tvers av brukere)
# ---------------------------------------------------------------------------

def create_family(name: str, owner_id: int) -> dict:
    import secrets as _secrets
    code = _secrets.token_hex(3).upper()  # 6 hex-tegn, f.eks. "A3F7B2"
    with _conn() as conn:
        cursor = conn.execute(
            "INSERT INTO family (name, invite_code, owner_id) VALUES (?, ?, ?)",
            (name, code, owner_id),
        )
        family_id = cursor.lastrowid
        conn.execute(
            "INSERT INTO family_member (family_id, user_id, role) VALUES (?, ?, 'owner')",
            (family_id, owner_id),
        )
    return {"id": family_id, "name": name, "invite_code": code}


def get_family_by_invite_code(code: str) -> dict | None:
    with _conn() as conn:
        row = conn.execute(
            "SELECT * FROM family WHERE invite_code = ?", (code.upper().strip(),)
        ).fetchone()
    return dict(row) if row else None


def join_family(family_id: int, user_id: int) -> None:
    with _conn() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO family_member (family_id, user_id, role) VALUES (?, ?, 'member')",
            (family_id, user_id),
        )


def get_user_families(user_id: int) -> list[dict]:
    with _conn() as conn:
        rows = conn.execute(
            """SELECT f.*, fm.role as my_role FROM family f
               JOIN family_member fm ON f.id = fm.family_id
               WHERE fm.user_id = ? ORDER BY f.created_at""",
            (user_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def get_family_members(family_id: int) -> list[dict]:
    with _conn() as conn:
        rows = conn.execute(
            """SELECT fm.role, fm.joined_at, u.id as user_id, u.email, u.name
               FROM family_member fm JOIN user u ON fm.user_id = u.id
               WHERE fm.family_id = ? ORDER BY fm.role DESC, fm.joined_at""",
            (family_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def leave_family(family_id: int, user_id: int) -> None:
    with _conn() as conn:
        conn.execute(
            "DELETE FROM family_member WHERE family_id = ? AND user_id = ?",
            (family_id, user_id),
        )


def delete_family(family_id: int) -> None:
    with _conn() as conn:
        conn.execute("DELETE FROM family WHERE id = ?", (family_id,))
