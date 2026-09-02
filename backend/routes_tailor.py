"""Tailoring routes (Agent B). Blueprint mounted at /api/tailor in app.py.

POST /<job_id>                      run tailoring -> resume_html document
POST /<job_id>/render               resume HTML -> 1-page PDF (resume_pdf)
POST /<job_id>/cover-letter         generate cover letter markdown (cover_letter_md)
POST /<job_id>/cover-letter/render  cover letter -> PDF (cover_letter_pdf)
POST /<job_id>/save                 {kind, content} save user edits as a new doc version
GET  /<job_id>/materials            latest docs per kind (+ content for text kinds)
POST /<job_id>/approve              status -> ready
"""
import json
import os
import re
import time

from flask import Blueprint, jsonify, request

from backend import cover_letter, db, docgen, tailoring, voice_check
from backend.app import load_config
from backend.profile_store import file_stem, load_profile

bp = Blueprint("tailor", __name__)

TEXT_KINDS = ("resume_html", "cover_letter_md")


def _job_or_none(job_id):
    return db.get_job(job_id)


def _docs_dir(job_id):
    d = os.path.join(db.DATA_DIR, "documents", f"job_{job_id}")
    os.makedirs(d, exist_ok=True)
    return d


def _latest_doc_id(job_id, kind):
    doc = db.latest_document(job_id, kind)
    return doc["id"] if doc else None


def _sanitize_company(name):
    return re.sub(r"[^A-Za-z0-9]+", "_", str(name or "Company")).strip("_") or "Company"


def _doc_meta(doc):
    try:
        return json.loads(doc.get("meta") or "{}")
    except (TypeError, ValueError):
        return {}


# ---------------------------------------------------------------- tailoring

@bp.post("/<int:job_id>")
def tailor_job(job_id):
    job = _job_or_none(job_id)
    if not job:
        return jsonify({"error": "job not found"}), 404
    body = request.get_json(silent=True) or {}
    feedback = str(body.get("feedback") or "").strip()
    # Persist per job: re-tailors keep honoring it until the user clears the box.
    db.set_setting(f"tailor_feedback:{job_id}", feedback)
    if feedback:
        db.log_event(job_id, "feedback", feedback[:300])
    prev_status = job["status"]
    db.update_job(job_id, status="tailoring")
    try:
        result = tailoring.tailor(job, load_profile(), load_config(), feedback=feedback or None)
        resume = result["resume"]
        html = docgen.render_resume_html(resume, load_profile())
        path = os.path.join(_docs_dir(job_id), "resume.html")
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        db.add_document(job_id, "resume_html", path,
                        meta={"mode": result["mode"], "structure": resume, "notes": result["notes"]})
        db.update_job(job_id, status="tailored")
        db.log_event(job_id, "tailored", f"mode={result['mode']}")
        return jsonify({
            "mode": result["mode"],
            "doc_id": _latest_doc_id(job_id, "resume_html"),
            "resume": resume,
            "notes": result["notes"],
            "voice": voice_check.check(html, kind="resume"),
        })
    except Exception as e:
        try:
            db.update_job(job_id, status=prev_status)
        except Exception:
            pass
        return jsonify({"error": f"tailoring failed: {e}"}), 500


@bp.post("/<int:job_id>/render")
def render_resume(job_id):
    job = _job_or_none(job_id)
    if not job:
        return jsonify({"error": "job not found"}), 404
    doc = db.latest_document(job_id, "resume_html")
    if not doc:
        return jsonify({"error": "no tailored resume yet — run Tailor first"}), 400
    meta = _doc_meta(doc)
    profile = load_profile()
    pdf_name = f"{file_stem(profile)}_Resume_{_sanitize_company(job.get('company'))}.pdf"
    pdf_path = os.path.join(_docs_dir(job_id), pdf_name)
    html_path = os.path.join(_docs_dir(job_id), "resume_render.html")
    try:
        structure = meta.get("structure")
        if structure and not meta.get("edited"):
            # Structured render with the 1-page enforcement (trim + retry) loop.
            pages, used, trimmed = docgen.render_resume_pdf_one_page(
                structure, profile, html_path, pdf_path)
            if trimmed:
                db.log_event(job_id, "pdf_rendered",
                             f"trimmed {len(trimmed)} bullet(s) to fit 1 page: {', '.join(trimmed)}")
        else:
            # User-edited (or structureless) HTML: render as-is, no trimming.
            pages = docgen.render_pdf(doc["path"], pdf_path, expect_pages=1)
            trimmed = []
        ats = docgen.ats_check(pdf_path, job, profile)
        db.add_document(job_id, "resume_pdf", pdf_path,
                        meta={"pages": pages, "trimmed": trimmed, "filename": pdf_name,
                              "ats": ats})
        db.log_event(job_id, "pdf_rendered", f"{pdf_name} pages={pages}")
        return jsonify({"doc_id": _latest_doc_id(job_id, "resume_pdf"),
                        "pages": pages, "trimmed": trimmed, "filename": pdf_name,
                        "ats": ats})
    except Exception as e:
        return jsonify({"error": f"PDF render failed: {e}"}), 500


# ------------------------------------------------------------- cover letter

@bp.post("/<int:job_id>/cover-letter")
def make_cover_letter(job_id):
    job = _job_or_none(job_id)
    if not job:
        return jsonify({"error": "job not found"}), 404
    resume_doc = db.latest_document(job_id, "resume_html")
    structure = _doc_meta(resume_doc).get("structure") if resume_doc else None
    try:
        result = cover_letter.generate(job, load_profile(), structure, load_config())
        path = os.path.join(_docs_dir(job_id), "cover_letter.md")
        with open(path, "w", encoding="utf-8") as f:
            f.write(result["markdown"])
        db.add_document(job_id, "cover_letter_md", path,
                        meta={"mode": result["mode"], "needs_editing": result.get("needs_editing", False)})
        db.log_event(job_id, "cover_letter", f"mode={result['mode']}")
        return jsonify({"mode": result["mode"],
                        "doc_id": _latest_doc_id(job_id, "cover_letter_md"),
                        "markdown": result["markdown"],
                        "needs_editing": result.get("needs_editing", False),
                        "voice": voice_check.check(result["markdown"], kind="cover_letter")})
    except Exception as e:
        return jsonify({"error": f"cover letter generation failed: {e}"}), 500


@bp.post("/<int:job_id>/cover-letter/render")
def render_cover_letter(job_id):
    job = _job_or_none(job_id)
    if not job:
        return jsonify({"error": "job not found"}), 404
    doc = db.latest_document(job_id, "cover_letter_md")
    if not doc:
        return jsonify({"error": "no cover letter yet — generate one first"}), 400
    try:
        with open(doc["path"], encoding="utf-8") as f:
            markdown = f.read()
        profile = load_profile()
        html = docgen.render_cover_letter_html(markdown, profile, job)
        html_path = os.path.join(_docs_dir(job_id), "cover_letter_render.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)
        pdf_name = f"{file_stem(profile)}_CoverLetter_{_sanitize_company(job.get('company'))}.pdf"
        pdf_path = os.path.join(_docs_dir(job_id), pdf_name)
        pages = docgen.render_pdf(html_path, pdf_path, expect_pages=1)
        db.add_document(job_id, "cover_letter_pdf", pdf_path,
                        meta={"pages": pages, "filename": pdf_name})
        db.log_event(job_id, "pdf_rendered", f"{pdf_name} pages={pages}")
        return jsonify({"doc_id": _latest_doc_id(job_id, "cover_letter_pdf"),
                        "pages": pages, "filename": pdf_name})
    except Exception as e:
        return jsonify({"error": f"cover letter PDF render failed: {e}"}), 500


# ------------------------------------------------------- edits / materials

@bp.post("/<int:job_id>/save")
def save_edits(job_id):
    job = _job_or_none(job_id)
    if not job:
        return jsonify({"error": "job not found"}), 404
    body = request.get_json(silent=True) or {}
    kind, content = body.get("kind"), body.get("content")
    if kind not in TEXT_KINDS:
        return jsonify({"error": f"kind must be one of {list(TEXT_KINDS)}"}), 400
    if not isinstance(content, str) or not content.strip():
        return jsonify({"error": "content is required"}), 400
    prev = db.latest_document(job_id, kind)
    prev_meta = _doc_meta(prev) if prev else {}
    ext = "html" if kind == "resume_html" else "md"
    stem = "resume" if kind == "resume_html" else "cover_letter"
    path = os.path.join(_docs_dir(job_id), f"{stem}_edit_{int(time.time())}.{ext}")
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        meta = {"mode": prev_meta.get("mode", "manual"), "edited": True}
        if kind == "resume_html" and prev_meta.get("structure"):
            meta["structure"] = prev_meta["structure"]  # keep provenance for reference
        db.add_document(job_id, kind, path, meta=meta)
        db.log_event(job_id, "edited", f"user saved {kind}")
        vkind = "cover_letter" if kind == "cover_letter_md" else "resume"
        return jsonify({"doc_id": _latest_doc_id(job_id, kind), "kind": kind,
                        "voice": voice_check.check(content, kind=vkind)})
    except Exception as e:
        return jsonify({"error": f"save failed: {e}"}), 500


@bp.get("/<int:job_id>/materials")
def materials(job_id):
    job = _job_or_none(job_id)
    if not job:
        return jsonify({"error": "job not found"}), 404
    out = {"job": job, "documents": {}}
    for kind in db.DOCUMENT_KINDS:
        doc = db.latest_document(job_id, kind)
        if not doc:
            continue
        entry = {"doc_id": doc["id"], "kind": kind, "created_at": doc["created_at"],
                 "meta": _doc_meta(doc)}
        if kind in TEXT_KINDS:
            try:
                with open(doc["path"], encoding="utf-8") as f:
                    entry["content"] = f.read()
            except OSError:
                entry["content"] = ""
        out["documents"][kind] = entry
    out["feedback"] = db.get_setting(f"tailor_feedback:{job_id}", "") or ""
    return jsonify(out)


@bp.post("/<int:job_id>/approve")
def approve(job_id):
    job = _job_or_none(job_id)
    if not job:
        return jsonify({"error": "job not found"}), 404
    if not db.latest_document(job_id, "resume_html"):
        return jsonify({"error": "nothing to approve — tailor a resume first"}), 400
    db.update_job(job_id, status="ready")
    db.log_event(job_id, "status_change", "approved materials -> ready")
    # Snapshot the posting text: postings expire, and interview prep needs the
    # original. Best-effort — approval never fails because of the snapshot.
    try:
        description = (job.get("description") or "").strip()
        if description:
            posting_path = os.path.join(_docs_dir(job_id), "posting.txt")
            with open(posting_path, "w", encoding="utf-8") as f:
                f.write(description)
            db.add_document(job_id, "posting_txt", posting_path,
                            meta={"chars": len(description), "url": job.get("url")})
            db.log_event(job_id, "posting_snapshot", f"posting.txt ({len(description)} chars)")
    except Exception:
        pass
    return jsonify({"status": "ready", "job_id": job_id})
