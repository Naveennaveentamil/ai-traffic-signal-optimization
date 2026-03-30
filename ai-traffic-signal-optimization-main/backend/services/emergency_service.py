from typing import Dict


_emergency_state: Dict = {
    "active": False,
    "corridor": "north_south",  # or "east_west"
}


def set_emergency_mode(
    active: bool,
    corridor: str = "north_south",
) -> Dict:
    _emergency_state["active"] = active
    if corridor in ("north_south", "east_west"):
        _emergency_state["corridor"] = corridor
    return _emergency_state


def get_emergency_state() -> Dict:
    return _emergency_state

