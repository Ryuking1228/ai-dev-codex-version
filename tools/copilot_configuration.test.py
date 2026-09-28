#!/usr/bin/env python3
"""Validate the repository-native GitHub Copilot adapters.

The detailed Nexus workflows stay in skills/. These checks prevent the small Copilot-facing
instruction, agent, prompt, and discovery files from drifting to missing paths or accidentally
invoking the Codex-only model router.
"""

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]

AGENTS = {
    "nexus-app-builder.agent.md",
    "nexus-product.agent.md",
    "nexus-architect.agent.md",
    "nexus-delivery.agent.md",
}
PROMPTS = {
    "nexus-new-app.prompt.md",
    "nexus-product-design.prompt.md",
    "nexus-existing-app.prompt.md",
    "nexus-deliver-backlog.prompt.md",
}
SKILLS = {
    "nexus-new-app": "skills/app/start/SKILL.md",
    "nexus-product-design": "skills/product/start/SKILL.md",
    "nexus-architecture": "skills/start/SKILL.md",
    "nexus-backlog-delivery": "skills/deliver-backlog/SKILL.md",
}


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def frontmatter(path: Path) -> dict[str, str]:
    text = read(path)
    if not text.startswith("---\n"):
        raise AssertionError(f"{path.relative_to(ROOT)} has no YAML frontmatter")
    block = text.split("---\n", 2)[1]
    fields = {}
    for line in block.splitlines():
        match = re.match(r"^([A-Za-z][A-Za-z0-9-]*):\s*(.+)$", line)
        if match:
            fields[match.group(1)] = match.group(2).strip()
    return fields


def markdown_paths(path: Path) -> list[Path]:
    links = re.findall(r"\[[^]]+\]\(([^)#]+)(?:#[^)]+)?\)", read(path))
    return [(path.parent / link).resolve() for link in links if "://" not in link]


class CopilotConfigurationTest(unittest.TestCase):
    def test_repository_instruction_and_path_instruction_exist(self):
        repository = ROOT / ".github/copilot-instructions.md"
        scoped = ROOT / ".github/instructions/nexus-customization.instructions.md"
        self.assertTrue(repository.is_file())
        self.assertEqual(
            frontmatter(scoped).get("applyTo"),
            '"skills/**/SKILL.md,.github/skills/**/SKILL.md,.github/agents/*.agent.md,.github/prompts/*.prompt.md"',
        )
        body = read(repository)
        for mapping in ("/app:start", "/product:<name>", "/infra:<name>",
                        "/architect:<name>", "/scalardb:<name>"):
            self.assertIn(mapping, body)
        self.assertIn("Never invoke `codex exec`", " ".join(body.split()))

    def test_custom_agent_profiles_are_valid_and_inherit_copilot_model(self):
        directory = ROOT / ".github/agents"
        self.assertEqual({path.name for path in directory.glob("*.agent.md")}, AGENTS)
        for path in directory.glob("*.agent.md"):
            fields = frontmatter(path)
            self.assertTrue(fields.get("name"), path)
            self.assertTrue(fields.get("description"), path)
            self.assertIn("tools", fields, path)
            self.assertNotIn("model", fields, f"{path} must inherit the active Copilot model")
            self.assertIn("Do not run", read(path), path)

    def test_prompt_files_link_to_existing_canonical_skills(self):
        directory = ROOT / ".github/prompts"
        self.assertEqual({path.name for path in directory.glob("*.prompt.md")}, PROMPTS)
        for path in directory.glob("*.prompt.md"):
            linked = markdown_paths(path)
            self.assertGreaterEqual(len(linked), 2, path)
            self.assertTrue(all(candidate.is_file() for candidate in linked),
                            f"broken link in {path}: {linked}")
            self.assertIn("Do not run the Codex model router", " ".join(read(path).split()), path)

    def test_discovery_skills_are_thin_valid_adapters(self):
        directory = ROOT / ".github/skills"
        self.assertEqual({path.name for path in directory.iterdir() if path.is_dir()}, set(SKILLS))
        for name, canonical in SKILLS.items():
            path = directory / name / "SKILL.md"
            fields = frontmatter(path)
            self.assertEqual(fields.get("name"), name)
            self.assertTrue(fields.get("description"))
            self.assertLess(len(read(path)), 1_200, f"{path} copied too much canonical behavior")
            self.assertIn((ROOT / canonical).resolve(), markdown_paths(path))
            self.assertTrue(all(candidate.is_file() for candidate in markdown_paths(path)), path)

    def test_documentation_exposes_copilot_entry_points(self):
        readme = read(ROOT / "README.md")
        guide = read(ROOT / "docs/github-copilot-usage_ja.md")
        for value in (".github/copilot-instructions.md", "nexus-app-builder",
                      "/nexus-new-app", "docs/github-copilot-usage_ja.md"):
            self.assertIn(value, readme)
        for value in ("nexus-product", "nexus-architect", "nexus-delivery",
                      "Codex model router"):
            self.assertIn(value, guide)


if __name__ == "__main__":
    unittest.main()
