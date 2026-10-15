#!/usr/bin/env python3
"""Local-only JobPilot records: no network, accounts, inference or submissions."""
import argparse
import contextlib
import csv
from datetime import date, datetime
import io
import json
import os
from pathlib import Path
import subprocess
import sys

REPO = Path(__file__).resolve().parents[1]
VERSION = 1
DISPOSITIONS = (None, "expired", "applied", "not a fit")
APPLICATION_STATUSES = {"submitted", "interview", "assessment", "offer", "hired",
                        "rejected", "withdrawn", "role_closed", "unknown"}
INTERVIEW_STATUSES = {"requested", "tentative", "scheduled", "rescheduled",
                      "completed", "cancelled"}
TABLES = {
    "leads": ("id", "company", "title", "source", "date_found",
              "date_dispositioned", "jd_url", "location", "salary_range",
              "disposition", "review_status", "reason", "next_action", "application_id"),
    "applications": ("id", "company", "title", "native_id", "jd_url", "location",
                     "salary_range", "status", "submission", "current_stage",
                     "interview_types", "outcome_events"),
    "interviews": ("id", "application_id", "job", "interview_date", "timezone",
                   "interview_number", "interview_type", "interview_subject",
                   "recording_link", "status", "employer_round_label", "transcript_link"),
}


def templates():
    """All candidate facts and permissions start unknown/empty, not inherited."""
    return {
        "profile.json": {"schema_version": VERSION, "onboarding_status": "in_progress",
                         "contact": {}, "targets": {}, "location_preferences": {},
                         "salary_preferences": {}, "approved_resume": None,
                         "writing_sample": None, "evidence": [], "history": []},
        "experience.json": {"schema_version": VERSION, "claims": [], "stories": [],
                            "open_questions": [], "history": []},
        "answer-bank.json": {"schema_version": VERSION, "answers": [], "history": []},
        "consents.json": {"schema_version": VERSION, "grants": [], "revocations": []},
        "questions.json": {"schema_version": VERSION, "questions": []},
        "state.json": {"schema_version": VERSION, "task": None, "checkpoint": None,
                       "paused": True, "browser_owner": None, "writer": None,
                       "schedules": []},
        "leads.json": {"schema_version": VERSION, "leads": []},
        "applications.json": {"schema_version": VERSION, "applications": [],
                              "unresolved_evidence": []},
        "interviews.json": {"schema_version": VERSION, "interviews": []},
    }


def reject_symlinks(path):
    for part in (path, *path.parents):
        if part.is_symlink():
            raise ValueError(f"Refusing symlink workspace component: {part}")


@contextlib.contextmanager
def writer_lock(root):
    """Never steal a lock. The creator alone removes it on normal completion."""
    reject_symlinks(root)
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    lock = root / ".writer.lock"
    try:
        fd = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as exc:
        raise ValueError("Workspace is locked; verify its owner before retrying.") from exc
    try:
        with os.fdopen(fd, "w") as handle:
            handle.write(str(os.getpid()))
        yield
    finally:
        lock.unlink()


def initialize(root):
    created = []
    with writer_lock(root):
        for name in ("materials", "runs", "evidence", "interviews", "exports"):
            path = root / name
            reject_symlinks(path)
            path.mkdir(exist_ok=True, mode=0o700)
        for name, record in templates().items():
            path = root / name
            reject_symlinks(path)
            try:
                fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            except FileExistsError:
                continue
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(record, handle, ensure_ascii=False, indent=2)
                handle.write("\n")
            created.append(name)
    return created


def load_records(root):
    reject_symlinks(root)
    records, errors = {}, []
    for name in templates():
        path = root / name
        try:
            reject_symlinks(path)
            record = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(record, dict) or record.get("schema_version") != VERSION:
                raise ValueError("unsupported schema_version or non-object root")
            records[name] = record
        except (OSError, ValueError) as exc:
            # Do not print candidate contents or entire parser input.
            errors.append(f"{name}: unreadable, malformed or unsupported ({type(exc).__name__})")
    return records, errors


def validate(root):
    records, errors = load_records(root)
    rows = {}
    for name, prototype in templates().items():
        if name not in records:
            continue
        for key, default in prototype.items():
            if key == "schema_version":
                continue
            value = records[name].get(key)
            if isinstance(default, (list, dict)) and not isinstance(value, type(default)):
                errors.append(f"{name}.{key}: expected {type(default).__name__}")
        if name[:-5] in TABLES:
            key = name[:-5]
            value = records[name].get(key)
            rows[key] = value if isinstance(value, list) else []
    by_id = {}
    for table, items in rows.items():
        found = {}
        native_seen = set()
        for index, row in enumerate(items):
            label = f"{table}[{index}]"
            if not isinstance(row, dict):
                errors.append(f"{label}: expected object")
                continue
            identity = row.get("id")
            if not isinstance(identity, str) or not identity.strip() or identity in found:
                errors.append(f"{label}: missing/duplicate string id")
            else:
                found[identity] = row
            required = {"leads": ("company", "title", "source", "jd_url"),
                        "applications": ("company", "title", "jd_url"),
                        "interviews": ("application_id", "job")}[table]
            for field in required:
                if not isinstance(row.get(field), str) or not row[field].strip():
                    errors.append(f"{label}.{field}: required nonempty string")
            if table in {"leads", "applications"}:
                native = row.get("native_id")
                if native is not None and (not isinstance(native, str) or not native.strip()):
                    errors.append(f"{label}.native_id: use full string ID or null")
                if table == "applications" and isinstance(native, str):
                    pair = (str(row.get("company", "")).strip().casefold(), native)
                    if pair in native_seen:
                        errors.append(f"{label}: duplicate employer/full native identity")
                    native_seen.add(pair)
            if table == "leads":
                if "disposition" not in row or row.get("disposition") not in DISPOSITIONS:
                    errors.append(f"{label}.disposition: unsupported")
                if row.get("disposition") in ("expired", "not a fit"):
                    if not row.get("reason") or not has_evidence(row.get("evidence")):
                        errors.append(f"{label}: final disposition needs reason and evidence")
                for field in ("date_found", "date_dispositioned"):
                    if not is_date_or_unknown(row.get(field)):
                        errors.append(f"{label}.{field}: ISO date/datetime or null required")
            elif table == "applications":
                if not isinstance(row.get("status"), str) or row["status"] not in APPLICATION_STATUSES:
                    errors.append(f"{label}.status: unsupported")
                submission = row.get("submission")
                if not isinstance(submission, dict):
                    errors.append(f"{label}.submission: required object")
                else:
                    if submission.get("actor") not in ("user", "assistant", "unknown"):
                        errors.append(f"{label}.submission.actor: unsupported")
                    if submission.get("basis") not in ("employer_receipt", "user_report", "legacy_import"):
                        errors.append(f"{label}.submission.basis: not a receipt/report/import")
                    if not has_evidence(submission.get("evidence")):
                        errors.append(f"{label}.submission.evidence: supporting source required")
                if not has_evidence(row.get("evidence")):
                    errors.append(f"{label}.evidence: supporting source required")
            elif table == "interviews":
                if not isinstance(row.get("status"), str) or row["status"] not in INTERVIEW_STATUSES:
                    errors.append(f"{label}.status: unsupported")
                number = row.get("interview_number")
                if number is not None and (type(number) is not int or number < 1):
                    errors.append(f"{label}.interview_number: positive integer or null")
                if row.get("interview_date") and not row.get("timezone"):
                    errors.append(f"{label}.timezone: required for a dated appointment")
                if not is_date_or_unknown(row.get("interview_date")):
                    errors.append(f"{label}.interview_date: ISO date/datetime or null required")
        by_id[table] = found
    apps = by_id.get("applications", {})
    for index, row in enumerate(rows.get("leads", [])):
        if isinstance(row, dict) and row.get("disposition") == "applied":
            if row.get("application_id") not in apps:
                errors.append(f"leads[{index}].application_id: applied lead needs actual application")
    for index, row in enumerate(rows.get("interviews", [])):
        if isinstance(row, dict) and row.get("application_id") not in apps:
            errors.append(f"interviews[{index}].application_id: unknown application")
    grants = records.get("consents.json", {}).get("grants", [])
    if isinstance(grants, list):
        for index, grant in enumerate(grants):
            if not isinstance(grant, dict) or not all(grant.get(key) for key in ("id", "scope", "source", "granted_at")):
                errors.append(f"consents.grants[{index}]: actual scope/source/time/id required")
    return records, errors


def has_evidence(value):
    return (isinstance(value, list) and bool(value)
            and all(isinstance(item, dict) and item.get("kind") and item.get("reference")
                    for item in value))


def is_date_or_unknown(value):
    if value is None:
        return True
    if not isinstance(value, str) or not value:
        return False
    try:
        if "T" in value:
            datetime.fromisoformat(value.replace("Z", "+00:00"))
        else:
            date.fromisoformat(value)
        return True
    except ValueError:
        return False


def export(root):
    with writer_lock(root):
        records, errors = validate(root)
        if errors:
            raise ValueError("Validation failed; exports unchanged: " + "; ".join(errors))
        target = root / "exports"
        reject_symlinks(target)
        target.mkdir(exist_ok=True, mode=0o700)
        for table, fields in TABLES.items():
            buffer = io.StringIO(newline="")
            writer = csv.DictWriter(buffer, fieldnames=fields)
            writer.writeheader()
            for row in records[table + ".json"][table]:
                selected = {}
                for key in fields:
                    value = row.get(key)
                    if isinstance(value, (dict, list)):
                        value = json.dumps(value, ensure_ascii=False, sort_keys=True)
                    # Prevent formula execution if a source string is opened in a spreadsheet.
                    if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@")):
                        value = "'" + value
                    selected[key] = value
                writer.writerow(selected)
            path = target / (table + ".csv")
            reject_symlinks(path)
            temporary = target / ("." + table + f".{os.getpid()}.tmp")
            try:
                with temporary.open("x", encoding="utf-8", newline="") as handle:
                    os.chmod(temporary, 0o600)
                    handle.write(buffer.getvalue())
                os.replace(temporary, path)
            finally:
                temporary.unlink(missing_ok=True)


def doctor(root):
    _, errors = validate(root)
    try:
        relative = root.relative_to(REPO)
        check = subprocess.run(["git", "check-ignore", "-q", "--", str(relative / "profile.json")],
                               cwd=REPO, capture_output=True, timeout=5)
        if check.returncode != 0:
            errors.append("Private workspace is not confirmed ignored by Git; review ignore/tracked state.")
        tracked = subprocess.run(["git", "ls-files", "--", str(relative)], cwd=REPO,
                                 capture_output=True, timeout=5)
        if tracked.returncode or tracked.stdout:
            errors.append("Private workspace contains tracked files or tracked-state check failed.")
    except ValueError:
        errors.append("External workspace: Git ignore not checked; verify its storage/publication boundary.")
    except (OSError, subprocess.TimeoutExpired):
        errors.append("Git checks unavailable; privacy/tracked state not verified.")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, default=REPO / ".jobpilot")
    parser.add_argument("command", choices=("init", "doctor", "validate", "export"))
    args = parser.parse_args()
    requested = args.workspace.expanduser().absolute()
    if requested.is_symlink():
        parser.error("Workspace itself must not be a symlink")
    # Resolve normal platform ancestors such as macOS /tmp -> /private/tmp;
    # still reject symlinks inside the actual workspace and at its leaf.
    root = requested.parent.resolve() / requested.name
    try:
        if args.command == "init":
            created = initialize(root)
            print(f"Created {len(created)} empty private records; existing files preserved. No permissions granted.")
        elif args.command == "export":
            export(root)
            print("Exported three CSV views; canonical records unchanged.")
        else:
            errors = doctor(root) if args.command == "doctor" else validate(root)[1]
            if errors:
                print("\n".join(errors), file=sys.stderr)
                return 1
            print("Structure checks passed. Receipt truth and permissions require human/source review.")
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
