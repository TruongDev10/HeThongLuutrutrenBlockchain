import csv
from datetime import datetime

from config import EXPORT_DIR
from database.init_db import get_connection


def export_detection_logs_csv():
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    filename = EXPORT_DIR / f"detection_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, timestamp, product_id, object_name, detected_color, rgb_value,
                   hsv_value, detected_hex, standard_hex, standard_rgb, color_ratio,
                   color_distance, match_standard, target_color, result_hash,
                   confidence, status, image_path, blockchain_tx_hash, blockchain_status
            FROM detection_logs
            ORDER BY id DESC
            """
        ).fetchall()

    with filename.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.writer(file)
        writer.writerow(
            [
                "id",
                "timestamp",
                "product_id",
                "object_name",
                "detected_color",
                "rgb_value",
                "hsv_value",
                "detected_hex",
                "standard_hex",
                "standard_rgb",
                "color_ratio",
                "color_distance",
                "match_standard",
                "target_color",
                "result_hash",
                "confidence",
                "status",
                "image_path",
                "blockchain_tx_hash",
                "blockchain_status",
            ]
        )
        for row in rows:
            writer.writerow([row[key] for key in row.keys()])
    return filename
