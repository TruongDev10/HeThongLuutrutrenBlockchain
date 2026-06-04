import hashlib
import importlib.util
import json
import time
from pathlib import Path

import cv2
from flask import Flask, Response, jsonify, redirect, render_template, request, send_file, url_for

from analytics.statistics import get_blockchain_logs, get_color_statistics, get_detection_logs, get_summary
from blockchain.service import BlockchainJob, ledger
from config import (
    COLOR_NAMES,
    DEFAULT_CONFIDENCE,
    MAX_CONTENT_LENGTH,
    OUTPUT_VIDEO_DIR,
    SECRET_KEY,
    UPLOAD_IMAGE_DIR,
    UPLOAD_VIDEO_DIR,
)
from database.init_db import init_database, insert_detection_log
from detection.video_processor import VideoProcessor
from utils.camera import CameraStream
from utils.export_csv import export_detection_logs_csv
from utils.helpers import allowed_file, ensure_directories, timestamp_slug, unique_filename


app = Flask(__name__)
app.config["SECRET_KEY"] = SECRET_KEY
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH

ensure_directories()
init_database()

processor = VideoProcessor()
camera = CameraStream()


def make_color_result_hash(
    product_id,
    object_name,
    detected_color,
    status,
    detected_hex,
    standard_hex,
    detected_rgb=None,
    standard_rgb=None,
    color_distance=None,
    match_standard=False,
    color_ratio=0,
):
    payload = {
        "product_id": product_id,
        "object_name": object_name,
        "detected_color": detected_color,
        "status": status,
        "detected_hex": (detected_hex or "").upper(),
        "standard_hex": (standard_hex or "").upper(),
        "detected_rgb": _parse_rgb(detected_rgb),
        "standard_rgb": _parse_rgb(standard_rgb),
        "color_distance": None if color_distance in {None, ""} else round(float(color_distance), 2),
        "match_standard": _parse_bool(match_standard),
        "color_ratio": round(float(color_ratio or 0), 4),
    }
    canonical_payload = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical_payload.encode("utf-8")).hexdigest(), payload


def _parse_rgb(value):
    if value in {None, ""}:
        return []
    if isinstance(value, str):
        value = [part.strip() for part in value.split(",") if part.strip()]
    return [int(v) for v in value]


def _parse_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "ok", "valid"}
    return bool(value)


def load_supported_colors():
    path = Path(__file__).resolve().parent / "config" / "colors.py"
    spec = importlib.util.spec_from_file_location("target_color_config_api", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.COLOR_CONFIG


@app.route("/")
def index():
    return redirect(url_for("dashboard"))


@app.route("/dashboard")
def dashboard():
    return render_template(
        "dashboard.html",
        colors=COLOR_NAMES,
        color_labels={key: value["vi_name"] for key, value in load_supported_colors().items()},
        default_confidence=DEFAULT_CONFIDENCE,
    )


@app.route("/history")
def history():
    return render_template("history.html", logs=get_detection_logs(200), stats=get_color_statistics())


@app.route("/video_feed")
def video_feed():
    return Response(_generate_camera_stream(), mimetype="multipart/x-mixed-replace; boundary=frame")


def _generate_camera_stream():
    while True:
        try:
            frame = camera.read()
            if frame is None:
                continue
            annotated, _ = processor.process_frame(frame, persist_logs=True, save_defects=True, control_robot=True)
            ok, buffer = cv2.imencode(".jpg", annotated, [int(cv2.IMWRITE_JPEG_QUALITY), 82])
            if not ok:
                continue
            yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n"
        except GeneratorExit:
            break
        except Exception as exc:
            error_frame = _error_frame(str(exc))
            ok, buffer = cv2.imencode(".jpg", error_frame)
            if ok:
                yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n"


def _error_frame(message):
    frame = 255 * cv2.UMat(360, 640, cv2.CV_8UC3).get()
    frame[:] = (15, 23, 42)
    cv2.putText(frame, "Camera error", (40, 155), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0, 120, 255), 2)
    cv2.putText(frame, message[:65], (40, 205), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (226, 232, 240), 1)
    return frame


@app.route("/upload-image", methods=["POST"])
def upload_image():
    file = request.files.get("image")
    if not file or file.filename == "":
        return jsonify({"ok": False, "message": "Chưa chọn ảnh."}), 400
    if not allowed_file(file.filename, "image"):
        return jsonify({"ok": False, "message": "Định dạng ảnh không hợp lệ."}), 400

    filename = unique_filename(file.filename)
    input_path = UPLOAD_IMAGE_DIR / filename
    output_path = Path("outputs") / "images" / f"result_{Path(filename).stem}.jpg"
    file.save(input_path)
    payload = processor.process_image(input_path, Path(output_path))
    payload["output_url"] = url_for("outputs", filename=f"images/{Path(payload['output_path']).name}")
    return jsonify({"ok": True, "message": "Phân tích ảnh thành công.", "result": payload})


@app.route("/upload-video", methods=["POST"])
def upload_video():
    file = request.files.get("video")
    if not file or file.filename == "":
        return jsonify({"ok": False, "message": "Chưa chọn video."}), 400
    if not allowed_file(file.filename, "video"):
        return jsonify({"ok": False, "message": "Định dạng video không hợp lệ."}), 400

    filename = unique_filename(file.filename)
    input_path = UPLOAD_VIDEO_DIR / filename
    output_path = OUTPUT_VIDEO_DIR / f"result_{Path(filename).stem}_{timestamp_slug()}.mp4"
    file.save(input_path)
    payload = processor.process_video(input_path, output_path)
    payload["output_url"] = url_for("outputs", filename=f"videos/{output_path.name}")
    return jsonify({"ok": True, "message": "Phân tích video thành công.", "result": payload})


@app.route("/api/stats")
def api_stats():
    summary = get_summary()
    summary["realtime"] = processor.latest_payload
    summary["blockchain"] = ledger.get_status()
    return jsonify(summary)


@app.route("/api/logs")
def api_logs():
    limit = request.args.get("limit", 80)
    return jsonify({"logs": get_detection_logs(limit)})


@app.route("/api/colors")
def api_colors():
    colors = load_supported_colors()
    return jsonify(
        {
            "colors": [
                {
                    "name": name,
                    "vi_name": cfg["vi_name"],
                    "hex": cfg["hex"],
                    "rgb": list(cfg["rgb"]),
                    "hsl": list(cfg["hsl"]),
                    "cmyk": list(cfg["cmyk"]),
                    "hsv_ranges": cfg["hsv_ranges"],
                    "tolerance": cfg["tolerance"],
                }
                for name, cfg in colors.items()
            ],
            "ignored_color": "not_target_color",
        }
    )


@app.route("/set-target-color", methods=["POST"])
@app.route("/api/set-target-color", methods=["POST"])
def set_target_color():
    data = request.get_json(silent=True) or request.form
    target = data.get("target_color")
    if target not in COLOR_NAMES and target not in {None, "", "none"}:
        return jsonify({"ok": False, "message": "Màu chuẩn không hợp lệ."}), 400
    processor.set_target_color(target)
    return jsonify({"ok": True, "target_color": processor.target_color})


@app.route("/set-confidence", methods=["POST"])
def set_confidence():
    data = request.get_json(silent=True) or request.form
    processor.set_confidence(data.get("confidence", DEFAULT_CONFIDENCE))
    return jsonify({"ok": True, "confidence": processor.confidence})


@app.route("/api/camera/status")
def camera_status():
    return jsonify({"ok": True, "camera": camera.status()})


@app.route("/api/camera/source", methods=["POST"])
def camera_source():
    data = request.get_json(silent=True) or request.form
    try:
        camera_index = int(data.get("camera_index", 0))
        camera.set_source(camera_index)
    except (TypeError, ValueError):
        return jsonify({"ok": False, "message": "camera_index phai la so."}), 400
    except Exception as exc:
        return jsonify({"ok": False, "message": str(exc), "camera": camera.status()}), 400
    return jsonify({"ok": True, "camera": camera.status()})


@app.route("/api/blockchain/status")
def blockchain_status():
    return jsonify(ledger.get_status())


@app.route("/api/blockchain/records")
def blockchain_records():
    total_records = ledger.get_total_records()
    status = ledger.get_status()
    return jsonify(
        {
            "ok": total_records is not None,
            "total_records": total_records,
            "totalRecords": total_records,
            "records_on_chain": total_records,
            "blockchain": status,
        }
    )


@app.route("/api/blockchain/logs")
def blockchain_logs():
    return jsonify({"logs": get_blockchain_logs(request.args.get("limit", 80))})


@app.route("/api/blockchain/log", methods=["POST"])
def blockchain_manual_log():
    data = request.get_json(silent=True) or {}
    detected_color = data.get("detected_color", "red")
    if detected_color not in COLOR_NAMES:
        return jsonify({"ok": False, "message": "detected_color must be one of the configured target colors."}), 400

    product_id = data.get("product_id") or f"MANUAL-{int(time.time())}"
    object_name = data.get("object_name", "manual-test")
    status = data.get("status", "valid")
    result_hash, _ = make_color_result_hash(
        product_id=product_id,
        object_name=object_name,
        detected_color=detected_color,
        status=status,
        detected_hex=data.get("detected_hex", "#FF0000"),
        standard_hex=data.get("standard_hex", "#FF0000"),
        detected_rgb=data.get("rgb_value", "255,0,0"),
        standard_rgb=data.get("standard_rgb", "255,0,0"),
        color_distance=data.get("color_distance", 0),
        match_standard=data.get("match_standard", True),
        color_ratio=data.get("color_ratio", 1.0),
    )
    log_id, timestamp_iso = insert_detection_log(
        object_name=object_name,
        detected_color=detected_color,
        rgb_value=data.get("rgb_value", "255,0,0"),
        hsv_value=data.get("hsv_value", "0,255,255"),
        confidence=float(data.get("confidence", 1.0)),
        status=status,
        product_id=product_id,
        blockchain_status="pending",
        detected_hex=data.get("detected_hex", "#FF0000"),
        standard_hex=data.get("standard_hex", "#FF0000"),
        standard_rgb=data.get("standard_rgb", "255,0,0"),
        color_ratio=float(data.get("color_ratio", 1.0)),
        color_distance=float(data.get("color_distance", 0)),
        match_standard=True,
        target_color=data.get("target_color"),
        result_hash=result_hash,
    )
    queued = ledger.enqueue(
        BlockchainJob(
            log_id=log_id,
            product_id=product_id,
            object_name=object_name,
            color=detected_color,
            result=status,
            rgb_value=data.get("rgb_value", "255,0,0"),
            hsv_value=data.get("hsv_value", "0,255,255"),
            timestamp_iso=timestamp_iso,
            confidence=int(float(data.get("confidence", 1.0)) * 100),
            result_hash=result_hash,
        )
    )
    return jsonify({"ok": True, "queued": queued, "log_id": log_id, "result_hash": result_hash})


@app.route("/api/color-hash", methods=["POST"])
def color_hash():
    data = request.get_json(silent=True) or {}
    result_hash, payload = make_color_result_hash(
        product_id=data.get("product_id", ""),
        object_name=data.get("object_name", ""),
        detected_color=data.get("detected_color", ""),
        status=data.get("status", ""),
        detected_hex=data.get("detected_hex", ""),
        standard_hex=data.get("standard_hex", ""),
        detected_rgb=data.get("detected_rgb") or data.get("rgb_value"),
        standard_rgb=data.get("standard_rgb"),
        color_distance=data.get("color_distance"),
        match_standard=data.get("match_standard", False),
        color_ratio=data.get("color_ratio", 0),
    )
    expected_hash = data.get("expected_hash")
    return jsonify(
        {
            "ok": True,
            "result_hash": result_hash,
            "matches": None if not expected_hash else result_hash.lower() == expected_hash.lower(),
            "payload": payload,
        }
    )


@app.route("/api/blockchain/config", methods=["POST"])
def blockchain_config():
    data = request.get_json(silent=True) or request.form
    ledger.configure(
        provider_uri=data.get("provider_uri"),
        contract_address=data.get("contract_address"),
        account_address=data.get("account_address"),
        private_key=data.get("private_key"),
        chain_id=data.get("chain_id"),
    )
    status = ledger.get_status()
    return jsonify({"ok": bool(status["ready"]), "message": status["status"], "blockchain": status})


@app.route("/export-csv")
def export_csv():
    path = export_detection_logs_csv()
    return send_file(path, as_attachment=True, download_name=path.name)


@app.route("/outputs/<path:filename>")
def outputs(filename):
    return send_file(Path("outputs") / filename)


@app.errorhandler(413)
def too_large(_):
    return jsonify({"ok": False, "message": "File quá lớn. Giới hạn hiện tại là 600MB."}), 413


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True, threaded=True)
