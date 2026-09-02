"""Assist-mode packet: ordered copy-paste fields, documents, and the apply URL.

Used when the ATS isn't Greenhouse/Lever, playwright is unavailable, or the
resume PDF hasn't been rendered yet. The user pastes values into the form
themselves; nothing is automated.
"""
from backend.submit.detector import detect_ats

# Human labels for the profile.screener_answers keys.
SCREENER_LABELS = {
    "authorized_to_work_us": "Are you authorized to work in the U.S.?",
    "require_sponsorship": "Will you now or in the future require sponsorship?",
    "willing_to_relocate": "Are you willing to relocate?",
    "remote_ok": "Open to remote work?",
    "hybrid_ok": "Open to hybrid work?",
    "veteran_status": "Veteran status",
    "disability_status": "Disability status",
    "gender": "Gender",
    "race_ethnicity": "Race / ethnicity",
    "how_did_you_hear": "How did you hear about us?",
    "pronouns": "Pronouns",
    "salary_expectation": "Salary expectations",
}

DOC_LABELS = {
    "resume_pdf": "Resume (PDF)",
    "resume_html": "Resume (HTML)",
    "cover_letter_pdf": "Cover letter (PDF)",
    "cover_letter_md": "Cover letter (text)",
    "form_screenshot": "Form screenshot",
}


def assist_packet(job, profile, materials):
    """Build the copy-paste packet for a job.

    materials: list of document rows (db.list_documents order: newest first).
    Returns {ats, apply_url, fields: [{label, value}...], documents: [{doc_id, kind, label, path}...]}.
    """
    det = detect_ats(job.get("url"))
    profile = profile or {}

    fields = []

    def add(label, value):
        if value not in (None, ""):
            fields.append({"label": label, "value": str(value)})

    add("Full name", profile.get("name"))
    add("First name", profile.get("first_name"))
    add("Last name", profile.get("last_name"))
    add("Email", profile.get("email"))
    add("Phone", profile.get("phone"))
    add("Location", profile.get("location"))
    add("City", profile.get("city"))
    add("LinkedIn", profile.get("linkedin"))
    add("Website", profile.get("website"))
    add("Current title", profile.get("current_title"))
    add("Current company", profile.get("current_company"))

    for key, value in (profile.get("screener_answers") or {}).items():
        add(SCREENER_LABELS.get(key, key.replace("_", " ").capitalize()), value)

    # Latest document per kind (materials arrive newest-first).
    documents, seen = [], set()
    for d in materials or []:
        if d["kind"] in seen:
            continue
        seen.add(d["kind"])
        documents.append({
            "doc_id": d["id"],
            "kind": d["kind"],
            "label": DOC_LABELS.get(d["kind"], d["kind"]),
            "path": d["path"],
        })

    return {
        "ats": det["ats"],
        "apply_url": det["apply_url"],
        "fields": fields,
        "documents": documents,
    }
