"""Job discovery routes (Agents A + D). Prefix /api/jobs set in app.py.

GET  /                      list jobs (?status=a,b&min_score=&q=&dream=1)
GET  /<id>                  one job + score_reasons
POST /refresh               fetch all sources, upsert, score new jobs
POST /<id>/status           {status, notes?}
POST /manual                {url?, title?, company?, description?}
POST /dream/resolve         {name, url} -> detected ATS + sample postings
"""
import json
import re

from flask import Blueprint, jsonify, request

from backend import db, matching
from backend.app import load_config
from backend.profile_store import load_profile
from backend.sources import FETCHERS
from backend.sources import dream as dream_source
from backend.sources import manual as manual_source

bp = Blueprint("jobs", __name__)


@bp.get("/")
def list_jobs():
    statuses = [s.strip() for s in (request.args.get("status") or "").split(",") if s.strip()]
    bad = [s for s in statuses if s not in db.JOB_STATUSES]
    if bad:
        return jsonify({"error": f"invalid status filter: {', '.join(bad)}"}), 400
    raw_min = request.args.get("min_score")
    min_score = None
    if raw_min not in (None, ""):
        try:
            min_score = int(raw_min)
        except ValueError:
            return jsonify({"error": "min_score must be an integer"}), 400
    q = (request.args.get("q") or "").strip() or None
    dream_only = request.args.get("dream") in ("1", "true")
    return jsonify(db.list_jobs(statuses=statuses or None, min_score=min_score, query=q,
                                dream_only=dream_only))


@bp.get("/<int:job_id>")
def get_job(job_id):
    job = db.get_job(job_id)
    if not job:
        return jsonify({"error": f"job {job_id} not found"}), 404
    try:
        job["score_reasons"] = matching.extract_keywords_hit(job, load_profile())
    except Exception:
        job["score_reasons"] = []
    return jsonify(job)


@bp.post("/refresh")
def refresh():
    try:
        config = load_config()
        profile = load_profile()
    except Exception as e:
        return jsonify({"error": f"could not load config/profile: {e}"}), 500

    fetched = 0
    new = 0
    new_dream = 0
    per_source = {}
    errors = []
    for name, fetch in FETCHERS.items():
        if name == "dream":
            # Dream companies (Agent D): per-company error isolation lives in
            # fetch_all; report counts per dream source (dream-greenhouse, …).
            source_jobs, dream_errors = dream_source.fetch_all(config)
            errors.extend(dream_errors)
            for j in source_jobs:
                per_source[j["source"]] = per_source.get(j["source"], 0) + 1
        else:
            try:
                source_jobs = fetch(config)
            except Exception as e:  # one source failing must not kill the rest
                per_source[name] = 0
                errors.append(f"{name}: {e}")
                continue
            per_source[name] = len(source_jobs)
        fetched += len(source_jobs)
        for job in source_jobs:
            try:
                job_id, created = db.upsert_job(job)
                if created:
                    new += 1
                    if job.get("dream"):
                        new_dream += 1
                    score = matching.score_job(job, profile, config)
                    db.update_job(job_id, score=score)
                    db.log_event(job_id, "fetched", f"{job['source']}: {job.get('title')} (score {score})")
            except Exception as e:
                errors.append(f"{job.get('source', name)} job {job.get('external_id')}: {e}")
    return jsonify({"fetched": fetched, "new": new, "new_dream": new_dream,
                    "per_source": per_source, "errors": errors})


@bp.post("/<int:job_id>/status")
def set_status(job_id):
    data = request.get_json(silent=True) or {}
    status = data.get("status")
    if status not in db.JOB_STATUSES:
        return jsonify({"error": f"invalid status {status!r}; must be one of: {', '.join(db.JOB_STATUSES)}"}), 400
    job = db.get_job(job_id)
    if not job:
        return jsonify({"error": f"job {job_id} not found"}), 404
    fields = {"status": status}
    if data.get("notes") is not None:
        fields["notes"] = str(data["notes"])
    updated = db.update_job(job_id, **fields)
    db.log_event(job_id, "status_change", f"{job['status']} -> {status}")
    return jsonify(updated)


@bp.post("/manual")
def manual_ingest():
    data = request.get_json(silent=True) or {}
    job, err = manual_source.ingest(data)
    if err:
        return jsonify({"error": err}), 400
    try:
        config = load_config()
        profile = load_profile()
        job_id, created = db.upsert_job(job)
        score = matching.score_job(job, profile, config)
        db.update_job(job_id, score=score)
        db.log_event(job_id, "fetched", f"manual: {job['title']} (score {score})")
    except Exception as e:
        return jsonify({"error": f"could not save job: {e}"}), 500
    out = db.get_job(job_id)
    out["created"] = created
    out["score_reasons"] = matching.extract_keywords_hit(out, profile)
    return jsonify(out)


@bp.post("/dream/resolve")
def dream_resolve():
    """Validate a dream-company entry before saving: detect the ATS and do a live
    fetch so Settings can show what monitoring this company would yield."""
    data = request.get_json(silent=True) or {}
    name = str(data.get("name") or "").strip()
    url = str(data.get("url") or "").strip()
    if not name or not url:
        return jsonify({"error": "name and url are both required"}), 400
    if not re.match(r"^https?://", url, re.I):
        return jsonify({"error": "url must start with http:// or https://"}), 400
    entry = {"name": name, "url": url}
    try:
        resolved = dream_source.resolve(entry)
        ats = resolved["ats"]
        if ats == "generic":
            postings = dream_source.extract_job_links(url)
        else:
            postings = dream_source.fetch_postings(ats, resolved["slug"])
    except Exception as e:
        return jsonify({"error": f"could not fetch postings from {url}: {e}"}), 400
    # Cache the resolution so the next refresh skips probing.
    db.set_setting(f"dream_resolved:{name}", json.dumps(resolved))
    return jsonify({
        "ats": ats,
        "slug": resolved.get("slug"),
        "postings_found": len(postings),
        "sample_titles": [p["title"] for p in postings[:5]],
    })
