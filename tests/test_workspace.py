"""Isolated behavioral checks; never read a real candidate workspace."""
import csv
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location(
    "workspace", Path(__file__).resolve().parents[1] / "scripts/jobpilot_workspace.py")
workspace = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(workspace)


class WorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve() / "private"
        workspace.initialize(self.root)

    def tearDown(self):
        self.temp.cleanup()

    def write(self, name, value):
        (self.root / name).write_text(json.dumps(value), encoding="utf-8")

    def read(self, name):
        return json.loads((self.root / name).read_text(encoding="utf-8"))

    def test_init_is_empty_and_no_clobber(self):
        self.assertEqual([], self.read("consents.json")["grants"])
        self.assertEqual({}, self.read("profile.json")["contact"])
        self.assertTrue(self.read("state.json")["paused"])
        profile = self.read("profile.json")
        profile["contact"] = {"email": "candidate@example.invalid"}
        self.write("profile.json", profile)
        before = (self.root / "profile.json").read_bytes()
        self.assertEqual([], workspace.initialize(self.root))
        self.assertEqual(before, (self.root / "profile.json").read_bytes())
        self.assertEqual([], workspace.validate(self.root)[1])

    def test_missing_record_repaired_without_overwrite(self):
        before = (self.root / "answer-bank.json").read_bytes()
        (self.root / "interviews.json").unlink()
        self.assertEqual(["interviews.json"], workspace.initialize(self.root))
        self.assertEqual(before, (self.root / "answer-bank.json").read_bytes())

    def test_no_lock_stealing_or_symlink_writes(self):
        lock = self.root / ".writer.lock"
        lock.write_text("other owner")
        with self.assertRaises(ValueError):
            workspace.initialize(self.root)
        self.assertEqual("other owner", lock.read_text())
        lock.unlink()
        profile = self.root / "profile.json"
        profile.unlink()
        outside = Path(self.temp.name) / "outside.json"
        outside.write_text("untouched")
        profile.symlink_to(outside)
        with self.assertRaises(ValueError):
            workspace.initialize(self.root)
        self.assertEqual("untouched", outside.read_text())

    def test_applied_requires_receipt_and_real_application(self):
        lead = {"id": "lead-1", "company": "Example", "title": "Product Manager",
                "source": "official", "jd_url": "https://example.invalid/1",
                "disposition": "applied", "application_id": "app-1"}
        self.write("leads.json", {"schema_version": 1, "leads": [lead]})
        self.assertTrue(workspace.validate(self.root)[1])
        application = {"id": "app-1", "company": "Example", "title": "Product Manager",
                       "native_id": "000123", "jd_url": lead["jd_url"], "status": "submitted",
                       "submission": {"actor": "assistant", "basis": "clicked", "evidence": []},
                       "evidence": []}
        self.write("applications.json", {"schema_version": 1, "applications": [application],
                                         "unresolved_evidence": []})
        self.assertTrue(workspace.validate(self.root)[1])
        evidence = [{"kind": "user_report", "reference": "test-only message"}]
        application["submission"].update(basis="user_report", evidence=evidence)
        application["evidence"] = evidence
        self.write("applications.json", {"schema_version": 1, "applications": [application],
                                         "unresolved_evidence": []})
        self.assertEqual([], workspace.validate(self.root)[1])

    def test_interview_links_and_number(self):
        interview = {"id": "i-1", "application_id": "missing", "job": "Example PM",
                     "status": "scheduled", "interview_number": 0,
                     "interview_date": "2027-01-01T10:00:00"}
        self.write("interviews.json", {"schema_version": 1, "interviews": [interview]})
        errors = workspace.validate(self.root)[1]
        self.assertTrue(any("unknown application" in error for error in errors))
        self.assertTrue(any("positive integer" in error for error in errors))
        self.assertTrue(any("timezone" in error for error in errors))

    def test_final_disposition_rejects_malformed_evidence_and_dates(self):
        lead = {"id": "l-1", "company": "Example", "title": "PM", "source": "official",
                "jd_url": "https://example.invalid/1", "disposition": "expired",
                "reason": "Claimed closed", "evidence": "anything", "date_found": "yesterday"}
        self.write("leads.json", {"schema_version": 1, "leads": [lead]})
        errors = workspace.validate(self.root)[1]
        self.assertTrue(any("reason and evidence" in error for error in errors))
        self.assertTrue(any("ISO date" in error for error in errors))
        lead.update(evidence=[{"kind": "official_listing", "reference": "test-only closure capture"}],
                    date_found=None, date_dispositioned="2026-10-14")
        self.write("leads.json", {"schema_version": 1, "leads": [lead]})
        self.assertEqual([], workspace.validate(self.root)[1])

    def test_malformed_types_return_errors_not_exceptions(self):
        lead = {"id": "l-1", "company": "Example", "title": "PM", "source": "official",
                "jd_url": "https://example.invalid/1", "disposition": ["expired"]}
        app = {"id": "a-1", "company": "Example", "title": "PM", "native_id": None,
               "jd_url": "https://example.invalid/1", "status": {"bad": "submitted"},
               "submission": {"actor": [], "basis": [], "evidence": []}, "evidence": []}
        self.write("leads.json", {"schema_version": 1, "leads": [lead]})
        self.write("applications.json", {"schema_version": 1, "applications": [app],
                                         "unresolved_evidence": []})
        self.assertTrue(workspace.validate(self.root)[1])

    def test_null_and_distinct_ids_preserved_in_exports(self):
        leads = [{"id": "l-1", "company": "=UNTRUSTED()", "title": "PM", "source": "official",
                  "jd_url": "https://example.invalid/1", "native_id": "000123", "disposition": None},
                 {"id": "l-2", "company": "Example", "title": "PM", "source": "official",
                  "jd_url": "https://example.invalid/2", "native_id": "000124", "disposition": None}]
        self.write("leads.json", {"schema_version": 1, "leads": leads})
        before = (self.root / "leads.json").read_bytes()
        workspace.export(self.root)
        self.assertEqual(before, (self.root / "leads.json").read_bytes())
        with (self.root / "exports/leads.csv").open() as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(2, len(rows))
        self.assertEqual("", rows[0]["disposition"])
        self.assertEqual("'=UNTRUSTED()", rows[0]["company"])

    def test_invalid_export_preserves_old_views(self):
        workspace.export(self.root)
        path = self.root / "exports/leads.csv"
        before = path.read_bytes()
        self.write("leads.json", {"schema_version": 1, "leads": [{"id": "bad"}]})
        with self.assertRaises(ValueError):
            workspace.export(self.root)
        self.assertEqual(before, path.read_bytes())


if __name__ == "__main__":
    unittest.main()
