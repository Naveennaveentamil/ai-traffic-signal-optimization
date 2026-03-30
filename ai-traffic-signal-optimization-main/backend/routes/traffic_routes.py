import os
import uuid
from typing import Any, Dict, List

from flask import Blueprint, jsonify, request
from werkzeug.utils import secure_filename

from ai.traffic_model import load_or_train_model, predict_congestion
from ai.yolo_detection import classify_density
from models.mongo_models import save_prediction, save_signal_log, save_traffic_event
from services.emergency_service import get_emergency_state, set_emergency_mode
from services.traffic_service import (
    get_current_signal_state,
    get_last_emergency_detected,
    get_last_vehicle_total,
    process_video_source,
    update_signal_state_for_counts,
)
from utils.config import UPLOAD_FOLDER

traffic_bp = Blueprint("traffic", __name__)

ml_model = load_or_train_model()

ALLOWED_VIDEO_EXT = {".mp4", ".avi", ".mov", ".mkv", ".webm", ".m4v"}


def _allowed_video(filename: str) -> bool:
    ext = os.path.splitext((filename or "").lower())[1]
    return ext in ALLOWED_VIDEO_EXT


def _finalize_detection(
    counts: Dict[str, Any],
    emergency_detected: bool,
    per_frame: List[Dict[str, Any]],
) -> Dict[str, Any]:
    total = counts.get("total_vehicles")
    if total is None:
        total = sum(int(counts.get(k, 0)) for k in ("car", "motorcycle", "bus", "truck"))
    density = classify_density(int(total))

    save_traffic_event(counts, emergency_detected, per_frame)

    signal_state = update_signal_state_for_counts(counts, emergency_detected)
    save_signal_log(signal_state)

    return {
        "success": True,
        "counts": counts,
        "density": density,
        "emergency_detected": emergency_detected,
        "signal_state": signal_state,
        "per_frame": per_frame[:20],
        "per_frame_total": len(per_frame),
    }


@traffic_bp.route("/process_video", methods=["POST"])
def process_video():
    payload = request.get_json(silent=True) or {}
    source_type = payload.get("source", "file")
    path = payload.get("path", "../ai/dataset/sample_traffic.mp4")
    max_frames = int(payload.get("max_frames", 45))

    counts, emergency_detected, per_frame = process_video_source(
        source_type, path, max_frames=max_frames
    )

    return jsonify(_finalize_detection(counts, emergency_detected, per_frame))


@traffic_bp.route("/upload_video", methods=["POST"])
def upload_video():
    """
    Multipart upload: field name `video`.
    Saves to uploads/temp, runs YOLO, deletes file in a finally block.
    Optional form fields: max_frames (default 45).
    """
    if "video" not in request.files:
        return jsonify({"success": False, "error": "Missing file field 'video'"}), 400

    file = request.files["video"]
    if not file or not file.filename:
        return jsonify({"success": False, "error": "No file selected"}), 400

    safe_name = secure_filename(file.filename)
    if not safe_name or not _allowed_video(safe_name):
        return jsonify(
            {
                "success": False,
                "error": "Unsupported or invalid video type. Use mp4, avi, mov, mkv, webm, or m4v.",
            }
        ), 400

    ext = os.path.splitext(safe_name)[1].lower() or ".mp4"
    stored_name = f"{uuid.uuid4().hex}{ext}"
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    temp_path = os.path.join(UPLOAD_FOLDER, stored_name)

    max_frames = int(request.form.get("max_frames", 45))

    try:
        file.save(temp_path)
        counts, emergency_detected, per_frame = process_video_source(
            "file", temp_path, max_frames=max_frames
        )
        body = _finalize_detection(counts, emergency_detected, per_frame)
        body["upload_filename"] = safe_name
        return jsonify(body)
    finally:
        try:
            if os.path.isfile(temp_path):
                os.remove(temp_path)
        except OSError:
            pass


@traffic_bp.route("/get_signal", methods=["GET"])
def get_signal():
    signal = get_current_signal_state()
    emergency_state = get_emergency_state()
    return jsonify(
        {
            "success": True,
            "signal_state": signal,
            "emergency": emergency_state,
            "last_emergency_detected": get_last_emergency_detected(),
        }
    )


@traffic_bp.route("/emergency", methods=["POST"])
def emergency():
    payload = request.get_json(silent=True) or {}
    active = bool(payload.get("active", True))
    corridor = payload.get("corridor", "north_south")
    state = set_emergency_mode(active, corridor=str(corridor))
    return jsonify({"success": True, "emergency": state})


@traffic_bp.route("/predict", methods=["POST"])
def predict():
    payload = request.get_json(silent=True) or {}
    features = payload.get("features")

    prediction, level = predict_congestion(
        ml_model,
        features,
        last_vehicle_count=get_last_vehicle_total(),
    )

    save_prediction(prediction, level, features)

    return jsonify(
        {
            "success": True,
            "prediction": float(prediction),
            "level": level,
            "vehicle_count_used": get_last_vehicle_total(),
        }
    )
