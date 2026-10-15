"""Offline route tests; Flask is optional for the main Codex-only workflow."""
import importlib.util
import json
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

try:
    from flask import Flask
    HAS_FLASK = True
except ImportError:
    HAS_FLASK = False


@unittest.skipUnless(HAS_FLASK, "optional legacy Flask dependency unavailable")
class LegacySubmissionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path(__file__).resolve().parents[1]
        # Avoid importing app factory, dotenv files, config copies or a real DB.
        app_stub = types.ModuleType("backend.app")
        app_stub.ROOT = str(cls.root)
        app_stub.load_config = lambda: {}
        app_stub.resolve_path = lambda path: path
        app_stub.save_config = lambda cfg: None
        with patch.dict(sys.modules, {"backend.app": app_stub}):
            spec = importlib.util.spec_from_file_location(
                "legacy_routes_test", cls.root / "backend/routes_submit.py")
            cls.routes = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(cls.routes)
        cls.app = Flask("legacy_submission_test")
        cls.app.register_blueprint(cls.routes.bp, url_prefix="/api")

    def test_final_routes_cannot_click_or_mark_submitted(self):
        with patch.object(self.routes.filler, "confirm") as click, \
             patch.object(self.routes.db, "update_job") as update:
            for suffix in ("confirm", "manual-confirm"):
                result = self.app.test_client().post(f"/api/submit/42/{suffix}", json={})
                self.assertEqual(409, result.status_code)
                self.assertEqual("receipt_workflow_required", result.json["code"])
            click.assert_not_called()
            update.assert_not_called()

    def test_prepare_is_assist_only_even_for_ready_job(self):
        job = {"id": 42, "status": "ready", "url": "https://example.invalid/job"}
        with patch.object(self.routes.db, "get_job", return_value=job), \
             patch.object(self.routes, "load_profile", return_value={}), \
             patch.object(self.routes.detector, "detect_ats", return_value={"ats": "greenhouse", "apply_url": job["url"]}), \
             patch.object(self.routes.db, "list_documents", return_value=[]), \
             patch.object(self.routes.db, "log_event"), \
             patch.object(self.routes.filler, "prepare") as fill, \
             patch.object(self.routes.db, "update_job") as update:
            result = self.app.test_client().post("/api/submit/42/prepare", json={})
            self.assertEqual(200, result.status_code)
            self.assertEqual("assist", result.json["mode"])
            self.assertEqual([], result.json["packet"]["fields"])
            fill.assert_not_called()
            update.assert_not_called()

    def test_cancel_preserves_uncertain_status(self):
        with patch.object(self.routes.db, "get_job", return_value={"id": 42, "status": "submitting"}), \
             patch.object(self.routes.filler, "cancel", return_value=True), \
             patch.object(self.routes.db, "log_event"), \
             patch.object(self.routes.db, "update_job") as update:
            result = self.app.test_client().post("/api/submit/42/cancel")
            self.assertEqual(200, result.status_code)
            self.assertTrue(result.json["status_preserved"])
            update.assert_not_called()

    def test_new_example_has_no_inherited_screening_answers(self):
        profile = json.loads((self.root / "data/profile.example.json").read_text())
        self.assertFalse(any(profile["screener_answers"].values()))
        self.assertFalse(profile["country"])
        config = json.loads((self.root / "config.example.json").read_text())
        self.assertFalse(config["features"]["auto_submit_greenhouse_lever"])


if __name__ == "__main__":
    unittest.main()
