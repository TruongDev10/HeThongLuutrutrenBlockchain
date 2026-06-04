from config import COLOR_HEX, COLOR_LABELS_VI, COLOR_NAMES
from database.init_db import get_connection


def get_color_statistics():
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT color_name, total_count, date_time FROM color_statistics ORDER BY color_name"
        ).fetchall()
    data = {row["color_name"]: dict(row) for row in rows}
    return [
        {
            "color": color,
            "label": COLOR_LABELS_VI.get(color, color),
            "hex": COLOR_HEX.get(color, "#64748b"),
            "count": data.get(color, {}).get("total_count", 0),
            "updated_at": data.get(color, {}).get("date_time"),
        }
        for color in COLOR_NAMES
    ]


def get_detection_logs(limit=80):
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, timestamp, product_id, object_name, detected_color, rgb_value,
                   hsv_value, detected_hex, standard_hex, standard_rgb, color_ratio,
                   color_distance, match_standard, target_color, result_hash,
                   confidence, status, image_path, blockchain_tx_hash, blockchain_status
            FROM detection_logs
            ORDER BY id DESC
            LIMIT ?
            """,
            (int(limit),),
        ).fetchall()
    return [dict(row) for row in rows]


def get_summary():
    stats = get_color_statistics()
    logs = get_detection_logs(1)
    total = sum(item["count"] for item in stats)
    with get_connection() as conn:
        placeholders = ",".join("?" for _ in COLOR_NAMES)
        defects = conn.execute(
            f"""
            SELECT COUNT(*) AS total
            FROM detection_logs
            WHERE status IN ('wrong_color', 'NG')
              AND detected_color IN ({placeholders})
            """,
            tuple(COLOR_NAMES),
        ).fetchone()["total"]
    return {
        "total": total,
        "defects": defects,
        "wrong_color": defects,
        "ignored": 0,
        "last_event": logs[0] if logs else None,
        "stats": stats,
    }


def get_blockchain_logs(limit=80):
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, timestamp, product_id, object_name, detected_color, confidence,
                   status, result_hash, blockchain_tx_hash, blockchain_status
            FROM detection_logs
            WHERE blockchain_status IS NOT NULL
            ORDER BY id DESC
            LIMIT ?
            """,
            (int(limit),),
        ).fetchall()
    return [dict(row) for row in rows]
