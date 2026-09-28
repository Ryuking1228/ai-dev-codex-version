#!/usr/bin/env python3
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from codex_model_router import RoutingError, build_command, resolve_route


ROOT = Path(__file__).resolve().parents[2]


class CodexModelRouterTest(unittest.TestCase):
    def test_architect_manifest_tiers_route_to_default_balanced_models(self):
        design = resolve_route(ROOT, ROOT, "architect:design-api", environ={})
        investigate = resolve_route(ROOT, ROOT, "architect:investigate", environ={})
        self.assertEqual((design.tier, design.model, design.reasoning_effort),
                         ("opus", "gpt-5.6-sol", "xhigh"))
        self.assertEqual((investigate.tier, investigate.model, investigate.reasoning_effort),
                         ("sonnet", "gpt-5.6-terra", "medium"))
        self.assertEqual(design.tier_source, "skills/common/skill-dependencies.yaml")

    def test_frontmatter_tier_is_used_outside_manifest(self):
        route = resolve_route(ROOT, ROOT, "architect:report-status", environ={})
        self.assertEqual(route.tier, "haiku")
        self.assertEqual(route.model, "gpt-5.6-luna")
        self.assertIn("skills/report-status/SKILL.md", route.tier_source)

    def test_app_skill_declares_a_routable_tier(self):
        route = resolve_route(ROOT, ROOT, "app:start", environ={})
        self.assertEqual((route.tier, route.model, route.reasoning_effort),
                         ("sonnet", "gpt-5.6-terra", "medium"))
        self.assertIn("skills/app/start/SKILL.md", route.tier_source)

    def test_product_manifest_is_supported(self):
        route = resolve_route(ROOT, ROOT, "product:define-vision", environ={})
        self.assertEqual(route.tier, "opus")
        self.assertEqual((route.model, route.reasoning_effort), ("gpt-5.6-sol", "xhigh"))

    def test_project_profile_and_explicit_precedence(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            (target / "work").mkdir()
            (target / "work/pipeline-progress.json").write_text(json.dumps({
                "options": {"codex_cost_profile": "quality"}
            }))
            project = resolve_route(ROOT, target, "architect:design-api", environ={})
            explicit = resolve_route(ROOT, target, "architect:design-api",
                                     profile="economy", environ={})
            self.assertEqual((project.profile, project.model, project.reasoning_effort),
                             ("quality", "gpt-5.6-sol", "xhigh"))
            self.assertEqual((explicit.profile, explicit.model, explicit.reasoning_effort),
                             ("economy", "gpt-5.6-terra", "medium"))

    def test_environment_overrides_project_profile(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            (target / "work").mkdir()
            (target / "work/pipeline-progress.json").write_text(json.dumps({
                "options": {"codex_cost_profile": "quality"}
            }))
            route = resolve_route(ROOT, target, "architect:design-api",
                                  environ={"NEXUS_CODEX_COST_PROFILE": "balanced"})
            self.assertEqual(route.profile, "balanced")

    def test_build_command_uses_argument_array_and_reasoning_setting(self):
        route = resolve_route(ROOT, ROOT, "architect:design-api", environ={})
        command = build_command("codex", ROOT, ROOT, route, ["--auto", "value with spaces"])
        self.assertEqual(command[:4], ["codex", "exec", "--model", "gpt-5.6-sol"])
        self.assertIn('model_reasoning_effort="xhigh"', command)
        self.assertIn("/architect:design-api --auto 'value with spaces'", command[-1])
        self.assertIn('["--auto", "value with spaces"]', command[-1])

    def test_unknown_skill_fails_instead_of_silently_using_default(self):
        with self.assertRaises(RoutingError):
            resolve_route(ROOT, ROOT, "architect:not-a-skill", environ={})

    def test_cli_dry_run_does_not_launch_codex_and_preserves_skill_args(self):
        result = subprocess.run([
            sys.executable, str(ROOT / "tools/codex-model-router.py"),
            "run", "product:define-scope", "--target", str(ROOT),
            "--profile", "economy", "--dry-run", "--", "--auto", "--lang=ja",
        ], text=True, capture_output=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["route"]["model"], "gpt-5.6-luna")
        self.assertIn("--auto --lang=ja", payload["command"][-1])


if __name__ == "__main__":
    unittest.main()
