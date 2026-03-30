import os
import sys

# Project root must be on path so `ai` package resolves when running from backend/
_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_BACKEND_DIR)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from flask import Flask, send_from_directory
from flask_cors import CORS

from routes.traffic_routes import traffic_bp
from utils.config import FRONTEND_BUILD_DIR, MAX_UPLOAD_MB


def create_app() -> Flask:
    app = Flask(__name__, static_folder=None)
    CORS(app)
    app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_MB * 1024 * 1024

    app.register_blueprint(traffic_bp, url_prefix="/api")

    @app.route("/")
    def serve_index():
        return send_from_directory(FRONTEND_BUILD_DIR, "index.html")

    @app.route("/<path:path>")
    def serve_static(path: str):
        return send_from_directory(FRONTEND_BUILD_DIR, path)

    return app


if __name__ == "__main__":
    app = create_app()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
