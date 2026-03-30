import os

from dotenv import load_dotenv

load_dotenv()


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(BASE_DIR)

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "traffic_db")

FRONTEND_BUILD_DIR = os.path.join(PROJECT_ROOT, "frontend")

# Temporary uploads (multipart); cleaned up after YOLO runs
UPLOAD_FOLDER = os.path.join(PROJECT_ROOT, "uploads", "temp")
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "200"))

