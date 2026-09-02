"""Review / judgment-layer routes (Agent G). Mounted at /api/review in app.py.

POST /<job_id>/evaluate        run fit evaluation, persist to settings, return it
GET  /<job_id>/evaluate        stored evaluation or 404
POST /<job_id>/critique        deterministic draft critique of latest materials
POST /<job_id>/interview-prep  build interview_prep.md -> interview_prep_md doc
GET  /insights                 pure-SQL outcome funnel (score bands x status groups)

None of these endpoints ever mutates job status.
"""
import json
import os

from flask import Blueprint, jsonify

from backend import db, evaluation, interview_prep, line_menu, review_checks
from backend.app import load_config
from backend.profile_store import load_profile

bp = Blueprint("review", __name__)

STATUS_GROUPS = {
    "active": ["interested", "tailoring", "tailored", "ready"],
    "submitted": ["submitting", "submitted"],
    "interview": ["interview"],
    "rejected": ["rejected"],
}
SCORE_BANDS = ["90+", "80-89", "70-79", "60-69", "<60"]

_GROUP_SQL = """CASE
    WHEN status IN ('interested','tailoring','tailored','ready') THEN 'active'
    WHEN status IN ('submitting','submitted') THEN 'submitted'
    WHEN status = 'interview' THEN 'interview'
    WHEN status = 'rejected' THEN 'rejected'
END"""
_BAND_SQL = """CASE
    WHEN score >= 90 THEN '90+'
    WHEN score >= 80 THEN '80-89'
    WHEN score >= 70 THEN '70-79'
    WHEN score >= 60 THEN '60-69'
    ELSE '<60'
END"""


def _docs_dir(job_id):
    d = os.path.join(db.DATA_DIR, "documents", f"job_{job_id}")
    os.makedirs(d, exist_ok=True)
    return d


def _doc_meta(doc):
    try:
        return json.loads((doc or {}).get("meta") or "{}")
    except (TypeError, ValueError):
        return {}


def _read_text(path):
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except OSError:
        return ""


# --------------------------------------------------------------- evaluate

@bp.post("/<int:job_id>/evaluate")
def evaluate_job(job_id):
    job = db.get_job(job_id)
    if not job:
        return jsonify({"error": "job not found"}), 404
    try:
        result = evaluation.evaluate(job, load_profile(), load_config(), line_menu.load_inventory())
        result["job_id"] = job_id
        result["evaluated_at"] = db.utcnow()
        db.set_setting(f"evaluation:{job_id}", json.dumps(result))
        db.log_event(job_id, "evaluated",
                     f"recommendation={result['recommendation']} location={result['location']['verdict']}")
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"evaluation failed: {e}"}), 500


@bp.get("/<int:job_id>/evaluate")
def get_evaluation(job_id):
    stored = db.get_setting(f"evaluation:{job_id}")
    if not stored:
        return jsonify({"error": "no stored evaluation for this job — POST to evaluate first"}), 404
    try:
        return jsonify(json.loads(stored))
    except ValueError:
        return jsonify({"error": "stored evaluation is corrupt — re-run evaluate"}), 500


# --------------------------------------------------------------- critique

@bp.post("/<int:job_id>/critique")
def critique_job(job_id):
    job = db.get_job(job_id)
    if not job:
        return jsonify({"error": "job not found"}), 404
    resume_doc = db.latest_document(job_id, "resume_html")
    structure = _doc_meta(resume_doc).get("structure") if resume_doc else None
    if not structure:
        return jsonify({"error": "no tailored resume for this job — run Tailor first"}), 400
    cl_doc = db.latest_document(job_id, "cover_letter_md")
    cover_letter_md = _read_text(cl_doc["path"]) if cl_doc else None
    try:
        result = review_checks.critique(job, structure, cover_letter_md,
                                        line_menu.load_inventory(), load_profile())
        result["job_id"] = job_id
        result["has_cover_letter"] = bool(cover_letter_md)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"critique failed: {e}"}), 500


# --------------------------------------------------------- interview prep

@bp.post("/<int:job_id>/interview-prep")
def interview_prep_job(job_id):
    job = db.get_job(job_id)
    if not job:
        return jsonify({"error": "job not found"}), 404
    resume_doc = db.latest_document(job_id, "resume_html")
    structure = _doc_meta(resume_doc).get("structure") if resume_doc else None
    posting_doc = db.latest_document(job_id, "posting_txt")
    posting_text = _read_text(posting_doc["path"]) if posting_doc else (job.get("description") or "")
    try:
        markdown = interview_prep.build_prep(job, load_profile(), load_config(),
                                             line_menu.load_inventory(), structure, posting_text)
        path = os.path.join(_docs_dir(job_id), "interview_prep.md")
        with open(path, "w", encoding="utf-8") as f:
            f.write(markdown)
        db.add_document(job_id, "interview_prep_md", path,
                        meta={"mode": "basic", "has_resume_structure": bool(structure),
                              "posting_source": "posting_txt" if posting_doc else "job.description"})
        db.log_event(job_id, "interview_prep", "interview_prep.md generated")
        doc = db.latest_document(job_id, "interview_prep_md")
        return jsonify({"doc_id": doc["id"] if doc else None, "markdown": markdown})
    except Exception as e:
        return jsonify({"error": f"interview prep failed: {e}"}), 500


# ---------------------------------------------------------------- insights

@bp.get("/insights")
def insights():
    """Outcome funnel over jobs that entered the pipeline (pure SQL, no LLM)."""
    conn = db.get_conn()
    try:
        def rows_for(dim_sql):
            got = conn.execute(
                f"SELECT {dim_sql} AS dim, {_GROUP_SQL} AS grp, COUNT(*) AS n "
                f"FROM jobs WHERE ({_GROUP_SQL}) IS NOT NULL GROUP BY dim, grp"
            ).fetchall()
            table = {}
            for r in got:
                table.setdefault(r["dim"], {g: 0 for g in STATUS_GROUPS})[r["grp"]] = r["n"]
            return table

        band_table = rows_for(_BAND_SQL)
        score_bands = []
        for band in SCORE_BANDS:
            counts = band_table.get(band, {g: 0 for g in STATUS_GROUPS})
            score_bands.append({"band": band, **counts, "total": sum(counts.values())})

        source_table = rows_for("source")
        by_source = [{"source": src, **counts, "total": sum(counts.values())}
                     for src, counts in sorted(source_table.items(),
                                               key=lambda kv: -sum(kv[1].values()))]

        dream_table = rows_for("CASE WHEN dream = 1 THEN 'dream' ELSE 'not_dream' END")
        by_dream = []
        for grp_name in ("dream", "not_dream"):
            counts = dream_table.get(grp_name, {g: 0 for g in STATUS_GROUPS})
            by_dream.append({"group": grp_name, **counts, "total": sum(counts.values())})

        totals = {g: sum(row[g] for row in score_bands) for g in STATUS_GROUPS}
        totals["in_funnel"] = sum(totals[g] for g in STATUS_GROUPS)
        submitted_ever = totals["submitted"] + totals["interview"]
        totals["interview_per_submitted"] = (
            round(totals["interview"] / submitted_ever, 3) if submitted_ever else None)

        return jsonify({
            "score_bands": score_bands,
            "by_source": by_source,
            "by_dream": by_dream,
            "totals": totals,
            "status_groups": STATUS_GROUPS,
        })
    except Exception as e:
        return jsonify({"error": f"insights query failed: {e}"}), 500
    finally:
        conn.close()
