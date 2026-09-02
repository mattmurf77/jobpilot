"""JobPilot Flask app factory + config loading.

Config layering:
  config.example.json  - tracked, generic defaults (what a fresh clone gets)
  config.json          - gitignored, the user's own config; created from the
                         example on first run and written by Settings.
Material paths in config are resolved by `materials_path()`: absolute paths are
used as-is, relative paths are resolved from the project root.
"""
import json
import os
import shutil

from dotenv import load_dotenv
from flask import Flask, jsonify, send_from_directory

from backend import db

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB_DIR = os.path.join(ROOT, "web")
CONFIG_PATH = os.path.join(ROOT, "config.json")
CONFIG_EXAMPLE_PATH = os.path.join(ROOT, "config.example.json")

load_dotenv(os.path.join(ROOT, ".env"))


def _ensure_config():
    if not os.path.exists(CONFIG_PATH) and os.path.exists(CONFIG_EXAMPLE_PATH):
        shutil.copyfile(CONFIG_EXAMPLE_PATH, CONFIG_PATH)


def load_config():
    _ensure_config()
    with open(CONFIG_PATH) as f:
        return json.load(f)


def save_config(cfg):
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=2)


def resolve_path(path):
    """Absolute paths pass through; relative paths are rooted at the project."""
    if not path:
        return ""
    path = os.path.expanduser(str(path))
    return path if os.path.isabs(path) else os.path.join(ROOT, path)


def materials_path(key, cfg=None):
    cfg = cfg or load_config()
    return resolve_path((cfg.get("materials") or {}).get(key, ""))


def create_app():
    app = Flask(__name__, static_folder=None)
    db.init_db()
    _ensure_config()

    from backend.routes_jobs import bp as jobs_bp
    from backend.routes_tailor import bp as tailor_bp
    from backend.routes_submit import bp as submit_bp
    from backend.routes_review import bp as review_bp

    app.register_blueprint(jobs_bp, url_prefix="/api/jobs")
    app.register_blueprint(tailor_bp, url_prefix="/api/tailor")
    app.register_blueprint(submit_bp, url_prefix="/api")
    app.register_blueprint(review_bp, url_prefix="/api/review")

    @app.get("/")
    def index():
        return send_from_directory(WEB_DIR, "index.html")

    @app.get("/<path:path>")
    def static_files(path):
        return send_from_directory(WEB_DIR, path)

    @app.get("/api/health")
    def health():
        return jsonify({
            "ok": True,
            "anthropic_key": bool(os.environ.get("ANTHROPIC_API_KEY")),
            "playwright": _playwright_available(),
        })

    @app.get("/api/events")
    def events():
        return jsonify(db.list_events())

    # Serve generated documents (resume PDFs etc.) for preview/download.
    @app.get("/api/documents/file/<int:doc_id>")
    def document_file(doc_id):
        conn = db.get_conn()
        row = conn.execute("SELECT * FROM documents WHERE id=?", (doc_id,)).fetchone()
        conn.close()
        if not row:
            return jsonify({"error": "not found"}), 404
        path = row["path"]
        return send_from_directory(os.path.dirname(path), os.path.basename(path))

    return app


def _playwright_available():
    try:
        import playwright  # noqa: F401
        return True
    except ImportError:
        return False
