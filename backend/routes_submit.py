"""Submission assist + settings routes. Agent C.

Blueprint is mounted at /api in app.py, so paths here are /settings/* and /submit/*.
Legacy browser submission routes are disabled. Copy/paste assist remains
available; receipt-aware submissions use the Codex workflow, not click inference.
"""
import os

from flask import Blueprint, jsonify, request

from backend import db
from backend.app import ROOT, load_config, resolve_path, save_config
from backend.profile_store import load_profile, save_profile
from backend.submit import assist, detector
from backend.submit import playwright_filler as filler

bp = Blueprint("submit", __name__)

ENV_PATH = os.path.join(ROOT, ".env")
EXPECTED_CONFIG_KEYS = {"search", "watchlist", "materials", "tailoring", "features", "dream_companies"}


# ---------- settings ----------

@bp.get("/settings")
def get_settings():
    try:
        cfg = load_config()
        profile = load_profile()
    except Exception as e:
        return jsonify({"error": f"failed to load settings: {e}"}), 500
    materials_status = {
        key: {"path": path, "exists": bool(path) and os.path.exists(resolve_path(path))}
        for key, path in (cfg.get("materials") or {}).items()
    }
    return jsonify({
        "config": cfg,
        "profile": profile,
        "anthropic_key_set": bool(os.environ.get("ANTHROPIC_API_KEY")),
        "playwright": filler.available(),
        "materials_status": materials_status,
    })


@bp.post("/settings/config")
def post_config():
    cfg = request.get_json(silent=True)
    if not isinstance(cfg, dict):
        return jsonify({"error": "body must be a JSON object (the full config)"}), 400
    missing = EXPECTED_CONFIG_KEYS - set(cfg)
    if missing:
        return jsonify({"error": f"config is missing keys: {', '.join(sorted(missing))}"}), 400
    unknown = set(cfg) - EXPECTED_CONFIG_KEYS
    if unknown:
        return jsonify({"error": f"config has unknown keys: {', '.join(sorted(unknown))}"}), 400
    try:
        save_config(cfg)
    except Exception as e:
        return jsonify({"error": f"failed to save config: {e}"}), 500
    return jsonify({"ok": True, "config": cfg})


@bp.post("/settings/profile")
def post_profile():
    profile = request.get_json(silent=True)
    if not isinstance(profile, dict) or not profile:
        return jsonify({"error": "body must be a non-empty JSON object (the full profile)"}), 400
    try:
        save_profile(profile)
    except Exception as e:
        return jsonify({"error": f"failed to save profile: {e}"}), 500
    return jsonify({"ok": True, "profile": profile})


@bp.post("/settings/apikey")
def post_apikey():
    body = request.get_json(silent=True) or {}
    key = (body.get("key") or "").strip()
    if not key:
        return jsonify({"error": "key is required"}), 400
    try:
        lines = []
        if os.path.exists(ENV_PATH):
            with open(ENV_PATH) as f:
                lines = f.read().splitlines()
        lines = [l for l in lines if not l.startswith("ANTHROPIC_API_KEY=")]
        lines.append(f"ANTHROPIC_API_KEY={key}")
        with open(ENV_PATH, "w") as f:
            f.write("\n".join(lines) + "\n")
    except Exception:
        # Deliberately vague: never echo the key or path contents into logs/errors.
        return jsonify({"error": "failed to write .env"}), 500
    os.environ["ANTHROPIC_API_KEY"] = key
    return jsonify({"ok": True, "anthropic_key_set": True})


# ---------- submission ----------

@bp.post("/submit/<int:job_id>/prepare")
def prepare(job_id):
    job = db.get_job(job_id)
    if not job:
        return jsonify({"error": "job not found"}), 404
    if job["status"] != "ready":
        return jsonify({
            "error": f"job must be in 'ready' status to submit (currently '{job['status']}')."
                     " Approve the tailored materials first."
        }), 409

    det = detector.detect_ats(job.get("url"))
    try:
        profile = load_profile()
    except Exception as e:
        return jsonify({"error": f"failed to load profile: {e}"}), 500

    return _assist_response(
        job, profile, det,
        note="Legacy auto-fill/submit is disabled. Use the employer site or the authorized Codex workflow; save an actual receipt.",
    )


@bp.post("/submit/<int:job_id>/confirm")
def confirm(job_id):
    return _disabled_submission()


@bp.post("/submit/<int:job_id>/cancel")
def cancel(job_id):
    job = db.get_job(job_id)
    if not job:
        return jsonify({"error": "job not found"}), 404
    try:
        closed = filler.cancel(job_id)
    except Exception:
        closed = False
    # Closing a browser session does not establish whether an earlier final
    # action was accepted. Preserve status until exact evidence is reconciled.
    db.log_event(job_id, "session_closed", "status preserved; reconcile any uncertain prior submission")
    return jsonify({"ok": True, "session_closed": closed, "status_preserved": True})


@bp.post("/submit/<int:job_id>/manual-confirm")
def manual_confirm(job_id):
    return _disabled_submission()


@bp.get("/submit/<int:job_id>/assist")
def get_assist(job_id):
    job = db.get_job(job_id)
    if not job:
        return jsonify({"error": "job not found"}), 404
    try:
        profile = load_profile()
    except Exception as e:
        return jsonify({"error": f"failed to load profile: {e}"}), 500
    packet = assist.assist_packet(job, profile, db.list_documents(job_id))
    return jsonify({"mode": "assist", "packet": packet})


@bp.get("/submit/documents")
def all_documents():
    """All documents grouped by job id — lets the pipeline board show doc chips in one call."""
    conn = db.get_conn()
    rows = [db.row_to_dict(r) for r in conn.execute(
        "SELECT id, job_id, kind, path, created_at FROM documents"
        " ORDER BY created_at DESC, id DESC").fetchall()]
    conn.close()
    grouped = {}
    for r in rows:
        grouped.setdefault(str(r["job_id"]), []).append(r)
    return jsonify(grouped)


# ---------- helpers ----------


def _disabled_submission():
    return jsonify({
        "error": "Legacy submission recording is disabled: a click is not a receipt. Use the Codex workflow and confirmed evidence.",
        "code": "receipt_workflow_required",
    }), 409


def _assist_response(job, profile, det, note=None):
    packet = assist.assist_packet(job, profile, db.list_documents(job["id"]))
    db.log_event(job["id"], "submit_prepared", f"assist packet generated ({det['ats']})")
    out = {"mode": "assist", "ats": det["ats"], "packet": packet}
    if note:
        out["note"] = note
    return jsonify(out)


def _cover_letter_text(job_id):
    doc = db.latest_document(job_id, "cover_letter_md")
    if not doc:
        return None
    try:
        with open(doc["path"]) as f:
            return f.read()
    except OSError:
        return None
