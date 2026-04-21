from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

DB_PATH = Path(__file__).parent.parent / "data" / "shopping.db"


def _conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def get_db():
    conn = _conn()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS products (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id     TEXT NOT NULL,
                mall_id     TEXT NOT NULL,
                category_id TEXT NOT NULL,
                title       TEXT NOT NULL,
                url         TEXT NOT NULL,
                image_url   TEXT DEFAULT '',
                price       REAL,
                seller      TEXT DEFAULT '',
                rating      REAL,
                review_count INTEGER DEFAULT 0,
                category_name TEXT DEFAULT '',
                mall_name   TEXT DEFAULT '',
                is_new      INTEGER DEFAULT 1,
                crawled_at  TEXT NOT NULL,
                updated_at  TEXT NOT NULL,
                UNIQUE(item_id, mall_id)
            );

            CREATE INDEX IF NOT EXISTS idx_products_category ON products(category_id);
            CREATE INDEX IF NOT EXISTS idx_products_mall     ON products(mall_id);
            CREATE INDEX IF NOT EXISTS idx_products_price    ON products(price);
            CREATE INDEX IF NOT EXISTS idx_products_crawled  ON products(crawled_at);
            CREATE VIRTUAL TABLE IF NOT EXISTS products_fts
                USING fts5(title, seller, content='products', content_rowid='id');

            CREATE TRIGGER IF NOT EXISTS products_ai AFTER INSERT ON products BEGIN
                INSERT INTO products_fts(rowid, title, seller)
                VALUES (new.id, new.title, new.seller);
            END;
            CREATE TRIGGER IF NOT EXISTS products_au AFTER UPDATE ON products BEGIN
                INSERT INTO products_fts(products_fts, rowid, title, seller)
                VALUES ('delete', old.id, old.title, old.seller);
                INSERT INTO products_fts(rowid, title, seller)
                VALUES (new.id, new.title, new.seller);
            END;

            CREATE TABLE IF NOT EXISTS schedules (
                category_id     TEXT PRIMARY KEY,
                category_name   TEXT NOT NULL,
                cron_expression TEXT NOT NULL DEFAULT '0 6 * * *',
                enabled         INTEGER NOT NULL DEFAULT 1,
                last_run_at     TEXT,
                next_run_at     TEXT,
                updated_at      TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS daily_reports (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                report_date TEXT NOT NULL,
                summary     TEXT NOT NULL,
                created_at  TEXT NOT NULL
            );
        """)
        _seed_schedules(conn)


def _seed_schedules(conn: sqlite3.Connection) -> None:
    defaults = [
        ("fashion",     "패션/의류",      "0 6 * * *"),
        ("electronics", "전자제품/디지털", "0 9 * * *"),
        ("food",        "식품/건강",      "0 7 * * *"),
        ("beauty",      "뷰티/화장품",    "0 8 * * *"),
        ("furniture",   "가구/인테리어",   "0 10 * * 1"),
        ("sports",      "스포츠/레저",    "0 10 * * 3"),
        ("baby",        "육아/완구",      "0 11 * * *"),
        ("pet",         "반려동물",       "0 11 * * 5"),
    ]
    now = datetime.utcnow().isoformat()
    for cat_id, cat_name, cron in defaults:
        conn.execute("""
            INSERT OR IGNORE INTO schedules
                (category_id, category_name, cron_expression, enabled, updated_at)
            VALUES (?, ?, ?, 1, ?)
        """, (cat_id, cat_name, cron, now))


def upsert_products(products: list[dict[str, Any]]) -> tuple[int, int]:
    now = datetime.utcnow().isoformat()
    new_count = updated_count = 0
    with get_db() as conn:
        for p in products:
            existing = conn.execute(
                "SELECT id FROM products WHERE item_id=? AND mall_id=?",
                (p["item_id"], p["mall_id"])
            ).fetchone()
            if existing:
                conn.execute("""
                    UPDATE products SET
                        title=?, url=?, image_url=?, price=?, seller=?,
                        rating=?, review_count=?, is_new=0, updated_at=?
                    WHERE item_id=? AND mall_id=?
                """, (
                    p.get("title", ""), p.get("url", ""), p.get("image_url", ""),
                    p.get("price"), p.get("seller", ""),
                    p.get("rating"), p.get("review_count", 0), now,
                    p["item_id"], p["mall_id"]
                ))
                updated_count += 1
            else:
                conn.execute("""
                    INSERT INTO products
                        (item_id, mall_id, category_id, title, url, image_url,
                         price, seller, rating, review_count,
                         category_name, mall_name, is_new, crawled_at, updated_at)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,1,?,?)
                """, (
                    p["item_id"], p["mall_id"], p.get("category_id", ""),
                    p.get("title", ""), p.get("url", ""), p.get("image_url", ""),
                    p.get("price"), p.get("seller", ""),
                    p.get("rating"), p.get("review_count", 0),
                    p.get("category_name", ""), p.get("mall_name", ""),
                    p.get("crawled_at", now), now
                ))
                new_count += 1
    return new_count, updated_count


def search_products(
    q: str = "",
    category: str = "",
    mall: str = "",
    min_price: float = 0,
    max_price: float = 0,
    sort: str = "relevance",
    limit: int = 20,
    offset: int = 0,
    since_hours: int = 0,
) -> dict[str, Any]:
    with get_db() as conn:
        conditions: list[str] = []
        params: list[Any] = []

        if q:
            conditions.append(
                "id IN (SELECT rowid FROM products_fts WHERE products_fts MATCH ?)"
            )
            params.append(q + "*")
        if category:
            conditions.append("category_id = ?")
            params.append(category)
        if mall:
            conditions.append("mall_id = ?")
            params.append(mall)
        if min_price > 0:
            conditions.append("price >= ?")
            params.append(min_price)
        if max_price > 0:
            conditions.append("price <= ?")
            params.append(max_price)
        if since_hours > 0:
            cutoff = (datetime.utcnow() - timedelta(hours=since_hours)).isoformat()
            conditions.append("crawled_at >= ?")
            params.append(cutoff)

        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        order = {
            "price_asc":  "price ASC NULLS LAST",
            "price_desc": "price DESC NULLS LAST",
            "newest":     "crawled_at DESC",
            "rating":     "rating DESC NULLS LAST",
            "reviews":    "review_count DESC",
        }.get(sort, "crawled_at DESC")

        total = conn.execute(
            f"SELECT COUNT(*) FROM products {where}", params
        ).fetchone()[0]

        rows = conn.execute(
            f"SELECT * FROM products {where} ORDER BY {order} LIMIT ? OFFSET ?",
            params + [limit, offset]
        ).fetchall()

        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "query": {"q": q, "category": category, "mall": mall, "sort": sort},
            "items": [dict(r) for r in rows],
        }


def get_schedules() -> list[dict[str, Any]]:
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM schedules ORDER BY category_id").fetchall()
        return [dict(r) for r in rows]


def update_schedule(category_id: str, cron_expression: str | None, enabled: bool | None) -> dict[str, Any]:
    now = datetime.utcnow().isoformat()
    with get_db() as conn:
        if cron_expression is not None:
            conn.execute(
                "UPDATE schedules SET cron_expression=?, updated_at=? WHERE category_id=?",
                (cron_expression, now, category_id)
            )
        if enabled is not None:
            conn.execute(
                "UPDATE schedules SET enabled=?, updated_at=? WHERE category_id=?",
                (1 if enabled else 0, now, category_id)
            )
        row = conn.execute(
            "SELECT * FROM schedules WHERE category_id=?", (category_id,)
        ).fetchone()
        return dict(row) if row else {}


def save_daily_report(summary: dict[str, Any]) -> None:
    with get_db() as conn:
        conn.execute(
            "INSERT INTO daily_reports (report_date, summary, created_at) VALUES (?,?,?)",
            (
                datetime.utcnow().strftime("%Y-%m-%d"),
                json.dumps(summary, ensure_ascii=False),
                datetime.utcnow().isoformat(),
            )
        )


def get_category_stats() -> list[dict[str, Any]]:
    with get_db() as conn:
        rows = conn.execute("""
            SELECT
                category_id, category_name,
                COUNT(*) AS total,
                SUM(is_new) AS new_today,
                MIN(price) AS min_price,
                MAX(price) AS max_price,
                ROUND(AVG(price), 0) AS avg_price,
                MAX(crawled_at) AS last_crawled
            FROM products
            GROUP BY category_id
            ORDER BY category_id
        """).fetchall()
        return [dict(r) for r in rows]
