import os
import time
from typing import Any, Dict, List, Tuple

from ai.yolo_detection import (
    analyze_video_for_counts,
    classify_density,
    signal_seconds_for_density,
)
from .emergency_service import get_emergency_state

# Last processed counts for ML /predict when features omitted
_last_vehicle_total: int = 0
_last_counts: Dict[str, Any] = {}
_last_emergency_detected: bool = False

# In-memory signal state (4-way junction: NS vs EW corridors)
_signal_state: Dict[str, Any] = {
    "north_south": {"green": 20, "yellow": 3, "red": 20, "is_green": True},
    "east_west": {"green": 20, "yellow": 3, "red": 20, "is_green": False},
    "density": "MEDIUM",
    "active_green_duration_sec": 28,
    "last_updated": time.time(),
}


def get_last_vehicle_total() -> int:
    return _last_vehicle_total


def get_last_counts() -> Dict[str, Any]:
    return dict(_last_counts)


def get_last_emergency_detected() -> bool:
    return _last_emergency_detected


def process_video_source(
    source_type: str,
    path: str,
    max_frames: int = 45,
) -> Tuple[Dict[str, Any], bool, List[Dict[str, Any]]]:
    """
    Run YOLO + OpenCV on file or webcam; update cached counts for /predict.
    Set SHOW_VIDEO_WINDOW=1 to open cv2.imshow window.
    """
    show_window = os.environ.get("SHOW_VIDEO_WINDOW", "0") == "1"
    counts, emergency_detected, per_frame = analyze_video_for_counts(
        source_type,
        path,
        max_frames=max_frames,
        show_window=show_window,
    )

    global _last_vehicle_total, _last_counts, _last_emergency_detected
    _last_counts = counts
    _last_emergency_detected = bool(emergency_detected)
    tv = counts.get("total_vehicles")
    if tv is None:
        tv = sum(int(counts.get(k, 0)) for k in ("car", "motorcycle", "bus", "truck"))
    _last_vehicle_total = int(tv)

    return counts, emergency_detected, per_frame


def update_signal_state_for_counts(counts: Dict[str, Any], emergency_detected: bool) -> Dict[str, Any]:
    """
    Density: LOW / MEDIUM / HIGH from total vehicles.
    HIGH → longer green; LOW → shorter green (via signal_seconds_for_density).
    Emergency: force green on configured corridor.
    """
    global _signal_state

    total = counts.get("total_vehicles")
    if total is None:
        total = sum(int(counts.get(k, 0)) for k in ("car", "motorcycle", "bus", "truck"))
    total = int(total)

    density = classify_density(total)
    green_sec = signal_seconds_for_density(density)

    north_south = int(counts.get("north", 0)) + int(counts.get("south", 0))
    east_west = int(counts.get("east", 0)) + int(counts.get("west", 0))

    emergency_state = get_emergency_state()
    if emergency_detected or emergency_state.get("active"):
        corridor = emergency_state.get("corridor", "north_south")
        for key in ("north_south", "east_west"):
            _signal_state[key]["is_green"] = key == corridor
        # Long green for emergency corridor
        em_green = max(green_sec, 55)
        if corridor == "north_south":
            _signal_state["north_south"]["green"] = em_green
            _signal_state["east_west"]["red"] = em_green + _signal_state["east_west"]["yellow"]
        else:
            _signal_state["east_west"]["green"] = em_green
            _signal_state["north_south"]["red"] = em_green + _signal_state["north_south"]["yellow"]
        _signal_state["density"] = density
        _signal_state["active_green_duration_sec"] = em_green
        _signal_state["last_updated"] = time.time()
        return _signal_state

    if north_south >= east_west:
        _signal_state["north_south"]["is_green"] = True
        _signal_state["east_west"]["is_green"] = False
        active_sec = green_sec
        _signal_state["north_south"]["green"] = active_sec
        _signal_state["east_west"]["green"] = max(10, min(30, green_sec - 5))
    else:
        _signal_state["north_south"]["is_green"] = False
        _signal_state["east_west"]["is_green"] = True
        active_sec = green_sec
        _signal_state["east_west"]["green"] = active_sec
        _signal_state["north_south"]["green"] = max(10, min(30, green_sec - 5))

    # Red durations roughly complement partner green + yellow
    _signal_state["north_south"]["red"] = _signal_state["east_west"]["green"] + _signal_state["east_west"]["yellow"]
    _signal_state["east_west"]["red"] = _signal_state["north_south"]["green"] + _signal_state["north_south"]["yellow"]

    _signal_state["density"] = density
    _signal_state["active_green_duration_sec"] = active_sec
    _signal_state["last_updated"] = time.time()
    return _signal_state


def get_current_signal_state() -> Dict[str, Any]:
    return _signal_state
