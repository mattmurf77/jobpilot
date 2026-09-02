"""Playwright form-fill sessions for Greenhouse/Lever applications.

Playwright's sync API cannot run on a thread that has a running asyncio loop
(and must stay on one thread for its whole lifecycle), so each submission gets
a dedicated worker thread that owns the browser. Flask request handlers talk
to it through queues. The browser is launched HEADED so the user can watch and
intervene; the final submit click only happens on an explicit confirm() call.

Guardrails honored here:
- prepare() fills the form, screenshots it, then STOPS. It never clicks submit.
- CAPTCHAs are never solved or bypassed — only detected and reported.
- Sessions auto-expire (browser closed, nothing submitted) after 30 minutes.
"""
import os
import queue
import threading
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DOCS_DIR = os.path.join(ROOT, "data", "documents")

SESSION_TTL_SECONDS = 30 * 60
PREPARE_TIMEOUT = 180   # seconds to wait for launch + navigate + fill
CONFIRM_TIMEOUT = 90    # seconds to wait for the submit click to settle


class PlaywrightUnavailable(RuntimeError):
    """Playwright is not importable/usable — caller should use assist mode."""


class SessionError(RuntimeError):
    """A session-level failure (no live session, navigation failed, timeout...)."""


_sessions = {}   # job_id -> _Session
_lock = threading.Lock()

# Finds the first visible-ish input/textarea whose name/id/placeholder/aria-label
# or <label> text matches a regex. Used for fields without stable selectors.
_LABEL_FINDER_JS = """(pat) => {
  const re = new RegExp(pat, 'i');
  const els = Array.from(document.querySelectorAll(
    'input:not([type=hidden]):not([type=file]):not([type=submit]):not([type=checkbox]):not([type=radio]), textarea'));
  for (const el of els) {
    const labels = el.labels ? Array.from(el.labels).map(l => l.textContent || '').join(' ') : '';
    const hay = [el.name || '', el.id || '', el.placeholder || '',
                 el.getAttribute('aria-label') || '', labels].join(' ');
    if (re.test(hay)) return el;
  }
  return null;
}"""


def available():
    try:
        import playwright.sync_api  # noqa: F401
        return True
    except Exception:
        return False


class _Session(threading.Thread):
    def __init__(self, job_id, apply_url, ats, profile, resume_pdf_path,
                 cover_letter_pdf_path, cover_letter_text, headless):
        super().__init__(daemon=True, name=f"submit-session-{job_id}")
        self.job_id = job_id
        self.apply_url = apply_url
        self.ats = ats
        self.profile = profile or {}
        self.resume_pdf_path = resume_pdf_path
        self.cover_letter_pdf_path = cover_letter_pdf_path
        self.cover_letter_text = cover_letter_text
        self.headless = headless
        self.commands = queue.Queue()
        self.results = queue.Queue()
        self.status = "starting"
        self.screenshot_path = os.path.join(DOCS_DIR, f"job_{job_id}", "form_filled.png")

    # ---- everything below runs inside the session thread ----

    def run(self):
        try:
            from playwright.sync_api import sync_playwright
        except Exception as e:
            self.results.put({"ok": False, "kind": "unavailable",
                              "error": f"playwright unavailable: {e}"})
            self._deregister()
            return
        try:
            with sync_playwright() as pw:
                browser = pw.chromium.launch(headless=self.headless)
                try:
                    page = browser.new_page()
                    report = {"filled": [], "skipped": [], "notes": [], "ats": self.ats,
                              "apply_url": self.apply_url}
                    page.goto(self.apply_url, timeout=60000)
                    try:
                        page.wait_for_load_state("domcontentloaded", timeout=15000)
                    except Exception:
                        pass
                    self._fill_form(page, report)
                    self._detect_captcha(page, report)
                    shot = self._safe_screenshot(page, self.screenshot_path, report)
                    if shot:
                        report["screenshot_path"] = shot
                    self.status = "awaiting_confirmation"
                    self.results.put({"ok": True, "report": report})
                    # STOP here. Browser stays open; wait for confirm/cancel/expiry.
                    self._await_command(page, report)
                finally:
                    try:
                        browser.close()
                    except Exception:
                        pass
        except Exception as e:
            self.results.put({"ok": False, "kind": "error", "error": str(e)})
        finally:
            self._deregister()

    def _await_command(self, page, report):
        deadline = time.time() + SESSION_TTL_SECONDS
        while True:
            remaining = deadline - time.time()
            if remaining <= 0:
                self.status = "expired"
                return
            try:
                cmd = self.commands.get(timeout=min(remaining, 5))
            except queue.Empty:
                continue
            if cmd == "cancel":
                self.status = "cancelled"
                self.results.put({"ok": True, "cancelled": True})
                return
            if cmd == "confirm":
                result = self._do_confirm(page, report)
                self.status = "done" if result.get("ok") else "error"
                self.results.put(result)
                return

    def _do_confirm(self, page, report):
        """User explicitly confirmed: click the real submit button."""
        if self.ats == "greenhouse":
            selectors = ["#submit_app", "input[type=submit]", "button[type=submit]"]
        elif self.ats == "lever":
            selectors = ["button[type=submit]", "input[type=submit]"]
        else:
            selectors = ["button[type=submit]", "input[type=submit]", "#submit_app"]
        clicked = False
        for sel in selectors:
            try:
                el = page.query_selector(sel)
                if el:
                    el.click()
                    clicked = True
                    break
            except Exception:
                continue
        if not clicked:
            return {"ok": False, "kind": "error",
                    "error": "submit button not found — submit manually in the browser window"}
        try:
            page.wait_for_load_state("networkidle", timeout=20000)
        except Exception:
            pass
        time.sleep(1)  # let any confirmation banner render
        result_path = self._safe_screenshot(
            page, os.path.join(os.path.dirname(self.screenshot_path), "submit_result.png"))
        out = dict(report)
        out["result_screenshot_path"] = result_path
        try:
            out["url_after_submit"] = page.url
        except Exception:
            pass
        return {"ok": True, "report": out}

    # ---- form filling (every step best-effort) ----

    def _fill_form(self, page, report):
        p = self.profile
        full_name = p.get("name") or " ".join(
            x for x in [p.get("first_name"), p.get("last_name")] if x)

        if self.ats == "lever":
            self._fill_selector(page, ['input[name="name"]'], full_name, "full name", report)
            self._fill_selector(page, ['input[name="email"]'], p.get("email"), "email", report)
            self._fill_selector(page, ['input[name="phone"]'], p.get("phone"), "phone", report)
            self._fill_selector(page, ['input[name="urls[LinkedIn]"]'], p.get("linkedin"),
                                "LinkedIn", report)
            if "LinkedIn (field not found)" in report["skipped"]:
                report["skipped"].remove("LinkedIn (field not found)")
                self._fill_by_regex(page, "linkedin", p.get("linkedin"), "LinkedIn", report)
            self._fill_selector(page, ['input[name="location"]'], p.get("location"),
                                "location", report)
            resume_selectors = ['input[name="resume"]', 'input[type=file]']
            cover_file_selectors = ['input[name="coverLetter"][type=file]',
                                    'input[name*="cover" i][type=file]']
        else:  # greenhouse + generic forms share common ids
            self._fill_selector(page, ["#first_name", 'input[name="first_name"]'],
                                p.get("first_name"), "first name", report)
            self._fill_selector(page, ["#last_name", 'input[name="last_name"]'],
                                p.get("last_name"), "last name", report)
            self._fill_selector(page, ["#email", 'input[name="email"]'],
                                p.get("email"), "email", report)
            self._fill_selector(page, ["#phone", 'input[name="phone"]'],
                                p.get("phone"), "phone", report)
            self._fill_selector(
                page,
                ["#job_application_location", 'input[name*="location" i]',
                 'input[id*="location" i]', "#city", 'input[name*="city" i]'],
                p.get("location") or p.get("city"), "location", report)
            self._fill_by_regex(page, "linkedin", p.get("linkedin"), "LinkedIn", report)
            resume_selectors = ["#resume", "[data-source] input[type=file]", "input[type=file]"]
            cover_file_selectors = ["#cover_letter", 'input[name*="cover" i][type=file]',
                                    'input[id*="cover" i][type=file]']

        self._upload(page, resume_selectors, self.resume_pdf_path, "resume PDF", report)

        # Cover letter: prefer a dedicated file input; else paste text into a
        # cover-letter textarea. No generic file-input fallback (would clobber resume).
        cl_done = False
        if self.cover_letter_pdf_path and os.path.exists(self.cover_letter_pdf_path):
            cl_done = self._upload(page, cover_file_selectors, self.cover_letter_pdf_path,
                                   "cover letter PDF", report, quiet=True)
        if not cl_done and self.cover_letter_text:
            self._fill_by_regex(page, r"cover\s*letter", self.cover_letter_text,
                                "cover letter text", report)
        elif not cl_done and not self.cover_letter_pdf_path:
            report["skipped"].append("cover letter (none generated)")
        elif not cl_done:
            report["skipped"].append("cover letter (no matching field)")

    def _safe_screenshot(self, page, path, report=None):
        """Screenshot with retries; full-page capture flakes occasionally in chromium,
        so fall back to viewport-only. Never fatal — returns the path or None."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        last_err = None
        for full_page in (True, True, False):
            try:
                page.screenshot(path=path, full_page=full_page)
                return path
            except Exception as e:
                last_err = e
                time.sleep(0.5)
        if report is not None:
            report["notes"].append(f"screenshot failed ({last_err}) — review the form "
                                   "in the browser window instead")
        return None

    def _detect_captcha(self, page, report):
        try:
            if page.query_selector(
                    'iframe[src*="recaptcha"], iframe[src*="hcaptcha"], iframe[src*="captcha"]'):
                report["notes"].append(
                    "CAPTCHA detected — it will NOT be solved automatically. "
                    "Complete it yourself in the browser window before confirming.")
        except Exception:
            pass

    def _fill_selector(self, page, selectors, value, label, report):
        if value in (None, ""):
            report["skipped"].append(f"{label} (no profile value)")
            return
        for sel in selectors:
            try:
                el = page.query_selector(sel)
                if el:
                    el.fill(str(value))
                    report["filled"].append(label)
                    return
            except Exception:
                continue
        report["skipped"].append(f"{label} (field not found)")

    def _fill_by_regex(self, page, pattern, value, label, report):
        if value in (None, ""):
            report["skipped"].append(f"{label} (no profile value)")
            return
        try:
            handle = page.evaluate_handle(_LABEL_FINDER_JS, pattern)
            el = handle.as_element()
            if el:
                el.fill(str(value))
                report["filled"].append(label)
                return
        except Exception:
            pass
        report["skipped"].append(f"{label} (field not found)")

    def _upload(self, page, selectors, path, label, report, quiet=False):
        if not path or not os.path.exists(path):
            if not quiet:
                report["skipped"].append(f"{label} (file missing)")
            return False
        for sel in selectors:
            try:
                el = page.query_selector(sel)
                if el:
                    el.set_input_files(path)
                    report["filled"].append(label)
                    return True
            except Exception:
                continue
        if not quiet:
            report["skipped"].append(f"{label} (file input not found)")
        return False

    def _deregister(self):
        with _lock:
            if _sessions.get(self.job_id) is self:
                del _sessions[self.job_id]


# ---- public API (called from Flask request threads) ----

def prepare(job, profile, resume_pdf_path, cover_letter_pdf_path=None, *,
            apply_url=None, ats="other", cover_letter_text=None, headless=False):
    """Launch a browser session, fill the form, screenshot, and WAIT.

    Returns the fill report. The session stays alive (browser open) until
    confirm(), cancel(), or 30-minute expiry. headless=True is a test override;
    real submissions run headed so the user can watch.
    """
    if not available():
        raise PlaywrightUnavailable("playwright is not installed in this environment")
    job_id = job["id"]
    with _lock:
        existing = _sessions.get(job_id)
        if existing and existing.is_alive():
            raise SessionError(
                "a submission session is already open for this job — confirm or cancel it first")
        sess = _Session(job_id, apply_url or job.get("url"), ats, profile,
                        resume_pdf_path, cover_letter_pdf_path, cover_letter_text, headless)
        _sessions[job_id] = sess
    sess.start()
    try:
        result = sess.results.get(timeout=PREPARE_TIMEOUT)
    except queue.Empty:
        sess.commands.put("cancel")
        raise SessionError("timed out preparing the application form")
    if not result.get("ok"):
        if result.get("kind") == "unavailable":
            raise PlaywrightUnavailable(result.get("error", "playwright unavailable"))
        raise SessionError(result.get("error", "form fill failed"))
    return result["report"]


def confirm(job_id):
    """Click the real submit button in the live session (user already confirmed in UI)."""
    sess = _get_live(job_id)
    sess.commands.put("confirm")
    try:
        result = sess.results.get(timeout=CONFIRM_TIMEOUT)
    except queue.Empty:
        raise SessionError("timed out waiting for the submission to complete")
    if not result.get("ok"):
        raise SessionError(result.get("error", "submission failed"))
    return result.get("report", {})


def cancel(job_id):
    """Close the browser without submitting. Returns True if a session was closed."""
    with _lock:
        sess = _sessions.get(job_id)
    if not sess or not sess.is_alive():
        return False
    sess.commands.put("cancel")
    sess.join(timeout=15)
    return True


def has_session(job_id):
    with _lock:
        sess = _sessions.get(job_id)
    return bool(sess and sess.is_alive() and sess.status == "awaiting_confirmation")


def _get_live(job_id):
    with _lock:
        sess = _sessions.get(job_id)
    if not sess or not sess.is_alive() or sess.status != "awaiting_confirmation":
        raise SessionError(
            "no live submission session for this job (it may have expired after 30 min) — "
            "run prepare again")
    return sess
