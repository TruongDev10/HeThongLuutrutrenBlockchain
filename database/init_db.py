import sqlite3
import sys
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from config import COLOR_NAMES, DATABASE_PATH


SCHEMA = """
CREATE TABLE IF NOT EXISTS detection_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    product_id TEXT,
    object_name TEXT NOT NULL,
    detected_color TEXT NOT NULL,
    rgb_value TEXT NOT NULL,
    hsv_value TEXT NOT NULL,
    detected_hex TEXT,
    standard_hex TEXT,
    standard_rgb TEXT,
    color_ratio REAL DEFAULT 0,
    color_distance REAL,
    match_standard INTEGER DEFAULT 0,
    target_color TEXT,
    result_hash TEXT,
    confidence REAL NOT NULL,
    status TEXT NOT NULL,
    image_path TEXT,
    blockchain_tx_hash TEXT,
    blockchain_status TEXT DEFAULT 'pending'
);

CREATE TABLE IF NOT EXISTS color_statistics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    color_name TEXT NOT NULL UNIQUE,
    total_count INTEGER NOT NULL DEFAULT 0,
    date_time TEXT NOT NULL
);
"""

MIGRATIONS = {
    "product_id": "ALTER TABLE detection_logs ADD COLUMN product_id TEXT",
    "detected_hex": "ALTER TABLE detection_logs ADD COLUMN detected_hex TEXT",
    "standard_hex": "ALTER TABLE detection_logs ADD COLUMN standard_hex TEXT",
    "standard_rgb": "ALTER TABLE detection_logs ADD COLUMN standard_rgb TEXT",
    "color_ratio": "ALTER TABLE detection_logs ADD COLUMN color_ratio REAL DEFAULT 0",
    "color_distance": "ALTER TABLE detection_logs ADD COLUMN color_distance REAL",
    "match_standard": "ALTER TABLE detection_logs ADD COLUMN match_standard INTEGER DEFAULT 0",
    "target_color": "ALTER TABLE detection_logs ADD COLUMN target_color TEXT",
    "result_hash": "ALTER TABLE detection_logs ADD COLUMN result_hash TEXT",
    "blockchain_tx_hash": "ALTER TABLE detection_logs ADD COLUMN blockchain_tx_hash TEXT",
    "blockchain_status": "ALTER TABLE detection_logs ADD COLUMN blockchain_status TEXT DEFAULT 'pending'",
}


@contextmanager
def get_connection():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_database():
    with get_connection() as conn:
        conn.executescript(SCHEMA)
        existing_columns = {
            row["name"] for row in conn.execute("PRAGMA table_info(detection_logs)").fetchall()
        }
        for column, statement in MIGRATIONS.items():
            if column not in existing_columns:
                conn.execute(statement)
        now = datetime.now().isoformat(timespec="seconds")
        for color in COLOR_NAMES:
            conn.execute(
                """
                INSERT OR IGNORE INTO color_statistics (color_name, total_count, date_time)
                VALUES (?, 0, ?)
                """,
                (color, now),
            )


def insert_detection_log(
    object_name,
    detected_color,
    rgb_value,
    hsv_value,
    confidence,
    status,
    image_path=None,
    product_id=None,
    blockchain_status="pending",
    detected_hex=None,
    standard_hex=None,
    standard_rgb=None,
    color_ratio=0,
    color_distance=None,
    match_standard=False,
    target_color=None,
    result_hash=None,
):
    now = datetime.now().isoformat(timespec="seconds")
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO detection_logs
            (timestamp, product_id, object_name, detected_color, rgb_value, hsv_value,
             detected_hex, standard_hex, standard_rgb, color_ratio, color_distance,
             match_standard, target_color, result_hash, confidence, status, image_path,
             blockchain_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now,
                product_id,
                object_name,
                detected_color,
                rgb_value,
                hsv_value,
                detected_hex,
                standard_hex,
                standard_rgb,
                float(color_ratio or 0),
                color_distance,
                1 if match_standard else 0,
                target_color,
                result_hash,
                float(confidence),
                status,
                image_path,
                blockchain_status,
            ),
        )
        conn.execute(
            """
            INSERT INTO color_statistics (color_name, total_count, date_time)
            VALUES (?, 1, ?)
            ON CONFLICT(color_name) DO UPDATE SET
                total_count = total_count + 1,
                date_time = excluded.date_time
            """,
            (detected_color, now),
        )
        return cursor.lastrowid, now


def update_blockchain_result(log_id, tx_hash=None, blockchain_status="sent"):
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE detection_logs
            SET blockchain_tx_hash = ?, blockchain_status = ?
            WHERE id = ?
            """,
            (tx_hash, blockchain_status, int(log_id)),
        )


if __name__ == "__main__":
    init_database()
    print(f"Database initialized at {DATABASE_PATH}")
