"""SQLite layer for JobPilot. Single source of truth for schema and status enum."""
import json
import os
import sqlite3
from datetime import datetime, timezone

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
DB_PATH = os.path.join(DATA_DIR, "jobpilot.db")

# Job lifecycle. Keep UI badges (web/js/app.js STATUS_META) in sync.
JOB_STATUSES = [
    "new", "interested", "skipped", "tailoring", "tailored",
    "ready", "submitting", "submitted", "interview", "rejected", "archived",
]

DOCUMENT_KINDS = [
    "resume_html", "resume_pdf", "resume_docx", "cover_letter_md", "cover_letter_pdf", "form_screenshot",
    "interview_prep_md", "posting_txt",
]


def utcnow():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def get_conn():
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_conn()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            external_id TEXT NOT NULL,
            url TEXT,
            title TEXT NOT NULL,
            company TEXT,
            location TEXT,
            remote INTEGER DEFAULT 0,
            salary TEXT,
            description TEXT,
            posted_at TEXT,
            score INTEGER DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'new',
            notes TEXT DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE (source, external_id)
        );
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
            kind TEXT NOT NULL,
            path TEXT NOT NULL,
            meta TEXT DEFAULT '{}',
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER REFERENCES jobs(id) ON DELETE CASCADE,
            type TEXT NOT NULL,
            detail TEXT DEFAULT '',
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        );
        """
    )
    # Migrations for DBs created before a column existed.
    cols = {r["name"] for r in conn.execute("PRAGMA table_info(jobs)").fetchall()}
    if "dream" not in cols:
        conn.execute("ALTER TABLE jobs ADD COLUMN dream INTEGER DEFAULT 0")
    conn.commit()
    conn.close()


def row_to_dict(row):
    return dict(row) if row is not None else None


# ---- jobs ----

def upsert_job(job):
    """Insert a job dict; on (source, external_id) conflict refresh volatile fields
    but never clobber user state (status, notes, score once user-touched).
    Returns (job_id, created: bool)."""
    conn = get_conn()
    now = utcnow()
    cur = conn.execute(
        "SELECT id, status FROM jobs WHERE source = ? AND external_id = ?",
        (job["source"], str(job["external_id"])),
    )
    existing = cur.fetchone()
    if existing:
        conn.execute(
            """UPDATE jobs SET url=?, title=?, company=?, location=?, remote=?,
               salary=?, description=?, posted_at=?, dream=max(dream, ?), updated_at=? WHERE id=?""",
            (
                job.get("url"), job["title"], job.get("company"), job.get("location"),
                int(bool(job.get("remote"))), job.get("salary"), job.get("description"),
                job.get("posted_at"), int(bool(job.get("dream"))), now, existing["id"],
            ),
        )
        conn.commit()
        conn.close()
        return existing["id"], False
    conn.execute(
        """INSERT INTO jobs (source, external_id, url, title, company, location, remote,
           salary, description, posted_at, score, status, dream, created_at, updated_at)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            job["source"], str(job["external_id"]), job.get("url"), job["title"],
            job.get("company"), job.get("location"), int(bool(job.get("remote"))),
            job.get("salary"), job.get("description"), job.get("posted_at"),
            int(job.get("score", 0)), job.get("status", "new"),
            int(bool(job.get("dream"))), now, now,
        ),
    )
    conn.commit()
    job_id = conn.execute(
        "SELECT id FROM jobs WHERE source=? AND external_id=?",
        (job["source"], str(job["external_id"])),
    ).fetchone()["id"]
    conn.close()
    return job_id, True


def list_jobs(statuses=None, min_score=None, query=None, dream_only=False, limit=500):
    conn = get_conn()
    sql = "SELECT * FROM jobs WHERE 1=1"
    params = []
    if dream_only:
        sql += " AND dream = 1"
    if statuses:
        sql += " AND status IN (%s)" % ",".join("?" * len(statuses))
        params += list(statuses)
    if min_score is not None:
        sql += " AND score >= ?"
        params.append(int(min_score))
    if query:
        sql += " AND (title LIKE ? OR company LIKE ? OR description LIKE ?)"
        params += [f"%{query}%"] * 3
    sql += " ORDER BY score DESC, posted_at DESC, id DESC LIMIT ?"
    params.append(limit)
    rows = [row_to_dict(r) for r in conn.execute(sql, params).fetchall()]
    conn.close()
    return rows


def get_job(job_id):
    conn = get_conn()
    row = row_to_dict(conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone())
    conn.close()
    return row


def update_job(job_id, **fields):
    if not fields:
        return get_job(job_id)
    if "status" in fields and fields["status"] not in JOB_STATUSES:
        raise ValueError(f"invalid status {fields['status']!r}")
    conn = get_conn()
    sets = ", ".join(f"{k}=?" for k in fields)
    conn.execute(
        f"UPDATE jobs SET {sets}, updated_at=? WHERE id=?",
        list(fields.values()) + [utcnow(), job_id],
    )
    conn.commit()
    conn.close()
    return get_job(job_id)


# ---- documents ----

def add_document(job_id, kind, path, meta=None):
    if kind not in DOCUMENT_KINDS:
        raise ValueError(f"invalid document kind {kind!r}")
    conn = get_conn()
    conn.execute(
        "INSERT INTO documents (job_id, kind, path, meta, created_at) VALUES (?,?,?,?,?)",
        (job_id, kind, path, json.dumps(meta or {}), utcnow()),
    )
    conn.commit()
    conn.close()


def list_documents(job_id):
    conn = get_conn()
    rows = [row_to_dict(r) for r in conn.execute(
        "SELECT * FROM documents WHERE job_id=? ORDER BY created_at DESC", (job_id,)
    ).fetchall()]
    conn.close()
    return rows


def latest_document(job_id, kind):
    conn = get_conn()
    row = row_to_dict(conn.execute(
        "SELECT * FROM documents WHERE job_id=? AND kind=? ORDER BY created_at DESC, id DESC LIMIT 1",
        (job_id, kind),
    ).fetchone())
    conn.close()
    return row


# ---- events ----

def log_event(job_id, type_, detail=""):
    conn = get_conn()
    conn.execute(
        "INSERT INTO events (job_id, type, detail, created_at) VALUES (?,?,?,?)",
        (job_id, type_, detail, utcnow()),
    )
    conn.commit()
    conn.close()


def list_events(job_id=None, limit=200):
    conn = get_conn()
    if job_id:
        rows = conn.execute(
            "SELECT * FROM events WHERE job_id=? ORDER BY id DESC LIMIT ?", (job_id, limit)
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM events ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    out = [row_to_dict(r) for r in rows]
    conn.close()
    return out


# ---- settings ----

def get_setting(key, default=None):
    conn = get_conn()
    row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    conn.close()
    return row["value"] if row else default


def set_setting(key, value):
    conn = get_conn()
    conn.execute(
        "INSERT INTO settings (key, value) VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, value),
    )
    conn.commit()
    conn.close()
