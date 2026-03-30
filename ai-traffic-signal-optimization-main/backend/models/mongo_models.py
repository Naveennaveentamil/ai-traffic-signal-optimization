import logging
from datetime import datetime
from typing import Any, Dict, Optional

from pymongo import MongoClient
from pymongo.errors import PyMongoError

from utils.config import MONGO_DB_NAME, MONGO_URI

logger = logging.getLogger(__name__)

_client: Optional[MongoClient] = None


def get_client() -> MongoClient:
    global _client
    if _client is None:
        _client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)
    return _client


def _db():
    return get_client()[MONGO_DB_NAME]


def _safe_insert(collection: str, doc: Dict[str, Any]) -> None:
    try:
        _db()[collection].insert_one(doc)
    except PyMongoError as e:
        logger.warning("MongoDB insert skipped (%s): %s", collection, e)


def save_traffic_event(
    counts: Dict[str, Any],
    emergency_detected: bool,
    per_frame: Any = None,
) -> None:
    doc = {
        "counts": counts,
        "emergency_detected": emergency_detected,
        "per_frame_sample": (per_frame[:5] if isinstance(per_frame, list) else None),
        "created_at": datetime.utcnow(),
    }
    _safe_insert("traffic_events", doc)


def save_signal_log(signal_state: Dict[str, Any]) -> None:
    doc = {
        "signal_state": signal_state,
        "created_at": datetime.utcnow(),
    }
    _safe_insert("signal_logs", doc)


def save_prediction(prediction: float, level: str, features: Any) -> None:
    doc = {
        "prediction": float(prediction),
        "level": level,
        "features": features,
        "created_at": datetime.utcnow(),
    }
    _safe_insert("predictions", doc)
