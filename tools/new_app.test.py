#!/usr/bin/env python3
"""Executable contracts for generator safety and source-bound release gates."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


generator = load(ROOT / "tools/new-app.py", "newapp")


class Contracts(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.app = Path(self.temp.name) / "test-app"
        generator.create(self.app, "test-app")
        self.ctl = load(self.app / "appctl.py", "appctl")

    def test_complete_project_and_no_overwrite(self):
        self.assertTrue((self.app / "LICENSE").exists())
        self.assertTrue((self.app / "frontend/package-lock.json").exists())
        self.assertIn("test-app", (self.app / "frontend/package.json").read_text())
        self.assertFalse((self.app / "frontend/node_modules").exists())
        self.assertFalse((self.app / "frontend/dist").exists())
        with self.assertRaises(ValueError): generator.create(self.app, "test-app")

    def test_invalid_name(self):
        with self.assertRaises(ValueError): generator.create(self.app.parent / "other", "../oops")

    def test_credentials_are_not_fingerprinted(self):
        before = self.ctl.fingerprint()
        self.ctl.initialize()
        self.assertEqual(before, self.ctl.fingerprint())
        self.assertEqual((self.app / ".env").stat().st_mode & 0o777, 0o600)

    def test_stale_source_blocks_release(self):
        source = self.ctl.fingerprint()
        self.ctl.record("verification.json", {"passed": True, "source": source})
        self.ctl.record("inspection.json", {"source": source, "note": "Observed actual workflow"})
        self.ctl.release_check()
        (self.app / "backend/app/main.py").write_text("# changed")
        with self.assertRaises(RuntimeError): self.ctl.release_check()

    def test_failed_verification_blocks_release(self):
        self.ctl.record("verification.json", {"passed": False, "source": self.ctl.fingerprint()})
        with self.assertRaises(RuntimeError): self.ctl.release_check()

    def test_missing_tests_never_pass(self):
        path = self.app / "empty.xml"
        for xml in ['<testsuites><testsuite tests="0"/></testsuites>',
                    '<testsuites><testsuite tests="2" skipped="1"/></testsuites>',
                    '<testsuite tests="1" failures="1"/>']:
            path.write_text(xml)
            with self.assertRaises(RuntimeError): self.ctl.junit_count(path)
        path.write_text('<testsuites><testsuite tests="7"/></testsuites>')
        self.assertEqual(self.ctl.junit_count(path), 7)

    def test_reject_public_destination_before_push(self):
        commands = []
        def fake_run(cmd, **kwargs):
            commands.append(cmd)
            return json.dumps({"visibility": "PUBLIC", "nameWithOwner": "Ryuking1228/test"})
        self.ctl.run = fake_run
        with self.assertRaises(RuntimeError): self.ctl.push("Ryuking1228/test")
        self.assertEqual(len(commands), 1)

    def test_reject_different_owner(self):
        with self.assertRaises(RuntimeError): self.ctl.push("wfukatsu/test")


if __name__ == "__main__":
    unittest.main()
