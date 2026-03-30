"""
Initialize MongoDB collections for the traffic project (optional sanity check).
Run: python database/mongo_setup.py  (from project root)
"""
import os
import sys

# Allow imports from backend
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "backend"))

from pymongo import MongoClient  # noqa: E402

from utils.config import MONGO_DB_NAME, MONGO_URI  # noqa: E402


def main() -> None:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    client.admin.command("ping")
    db = client[MONGO_DB_NAME]
    for name in ("traffic_events", "signal_logs", "predictions"):
        db[name].create_index("created_at")
    print(f"OK: connected to {MONGO_URI}, database={MONGO_DB_NAME}, collections ready.")


if __name__ == "__main__":
    main()
