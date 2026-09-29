"""Resolve AI Dev Loop skill model tiers to Codex models and build safe child-run commands."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
import json
import os
import re
import shlex


class RoutingError(ValueError):
    """Raised when a skill or routing profile cannot be resolved safely."""


@dataclass(frozen=True)
class Route:
    plugin: str
    skill: str
    tier: str
    profile: str
    model: str
    reasoning_effort: str
    skill_file: str
    tier_source: str
    profile_source: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


def repository_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RoutingError(f"Missing routing configuration: {path}") from exc
    except json.JSONDecodeError as exc:
        raise RoutingError(f"Invalid JSON in routing configuration {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise RoutingError(f"Routing configuration must be a JSON object: {path}")
    return data


def load_config(root: Path, path: Path | None = None) -> dict[str, Any]:
    config_path = path or root / "config/codex-model-routing.json"
    config = _read_json(config_path)
    profiles = config.get("profiles")
    if not isinstance(profiles, dict) or not profiles:
        raise RoutingError("Routing configuration has no profiles")
    default_profile = config.get("default_profile")
    if default_profile not in profiles:
        raise RoutingError(f"Unknown default_profile: {default_profile}")
    for profile_name, tiers in profiles.items():
        if not isinstance(tiers, dict):
            raise RoutingError(f"Profile {profile_name} must be an object")
        for tier in ("haiku", "sonnet", "opus"):
            route = tiers.get(tier)
            if not isinstance(route, dict) or not route.get("model") or not route.get("reasoning_effort"):
                raise RoutingError(f"Profile {profile_name} has no complete {tier} route")
    return config


def parse_skill_ref(skill_ref: str) -> tuple[str, str]:
    if skill_ref.count(":") != 1:
        raise RoutingError("Skill must use the form <plugin>:<skill>, for example architect:design-api")
    plugin, skill = skill_ref.split(":", 1)
    allowed = {"architect", "product", "infra", "scalardb", "app"}
    if plugin not in allowed:
        raise RoutingError(f"Unsupported plugin {plugin!r}; expected one of {sorted(allowed)}")
    if not skill or any(ch not in "abcdefghijklmnopqrstuvwxyz0123456789-" for ch in skill):
        raise RoutingError(f"Invalid skill name: {skill!r}")
    return plugin, skill


def _manifest_model(root: Path, plugin: str, skill: str) -> tuple[str | None, Path | None]:
    if plugin == "architect":
        path = root / "skills/common/skill-dependencies.yaml"
    elif plugin == "product":
        path = root / "skills/product/common/skill-dependencies.yaml"
    else:
        return None, None
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None, path
    match = re.search(rf"^  {re.escape(skill)}:[ \t]*(.*)$", text, re.MULTILINE)
    if not match:
        return None, path
    inline = match.group(1).strip()
    if inline:
        model = re.search(r"\bmodel:\s*([a-z0-9-]+)", inline)
        return (model.group(1) if model else None), path
    start = match.end()
    next_entry = re.search(r"^  [a-z][a-z0-9-]*:[ \t]*", text[start:], re.MULTILINE)
    body = text[start:start + next_entry.start()] if next_entry else text[start:]
    model = re.search(r"^    model:\s*([a-z0-9-]+)\s*$", body, re.MULTILINE)
    if model:
        return model.group(1), path
    return None, path


def find_skill_file(root: Path, plugin: str, skill: str) -> Path:
    candidates = []
    if plugin == "product":
        candidates.append(root / "skills/product" / skill / "SKILL.md")
    elif plugin == "infra":
        candidates.append(root / "skills/infra" / skill / "SKILL.md")
    elif plugin == "app":
        candidates.append(root / "skills/app" / skill / "SKILL.md")
    else:
        candidates.append(root / "skills" / skill / "SKILL.md")
    for path in candidates:
        if path.is_file():
            return path.resolve()
    shown = ", ".join(str(path.relative_to(root)) for path in candidates)
    raise RoutingError(f"Skill file not found for {plugin}:{skill}; checked {shown}")


def _frontmatter_model(path: Path) -> str | None:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return None
    try:
        block = text.split("---", 2)[1]
    except IndexError:
        return None
    model = re.search(r"^model:\s*([a-z0-9-]+)\s*$", block, re.MULTILINE)
    return model.group(1) if model else None


def resolve_tier(root: Path, plugin: str, skill: str, default_tier: str) -> tuple[str, str, Path]:
    skill_file = find_skill_file(root, plugin, skill)
    manifest_model, manifest_path = _manifest_model(root, plugin, skill)
    if manifest_model:
        return manifest_model, str(manifest_path.relative_to(root)), skill_file
    frontmatter_model = _frontmatter_model(skill_file)
    if frontmatter_model:
        return frontmatter_model, str(skill_file.relative_to(root)), skill_file
    return default_tier, "config.default_tier", skill_file


def _project_profile(target: Path) -> str | None:
    path = target / "work/pipeline-progress.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None
    options = data.get("options") if isinstance(data, dict) else None
    value = options.get("codex_cost_profile") if isinstance(options, dict) else None
    return value if isinstance(value, str) and value else None


def resolve_profile(config: dict[str, Any], target: Path, explicit: str | None = None,
                    environ: dict[str, str] | None = None) -> tuple[str, str]:
    env = os.environ if environ is None else environ
    candidates = [
        (explicit, "command line"),
        (env.get("AI_DEV_LOOP_CODEX_COST_PROFILE"), "AI_DEV_LOOP_CODEX_COST_PROFILE"),
        (_project_profile(target), "work/pipeline-progress.json"),
        (config.get("default_profile"), "config.default_profile"),
    ]
    profiles = config["profiles"]
    for value, source in candidates:
        if not value:
            continue
        if value not in profiles:
            raise RoutingError(f"Unknown Codex cost profile {value!r} from {source}; choose {sorted(profiles)}")
        return value, source
    raise RoutingError("No Codex cost profile could be resolved")


def resolve_route(root: Path, target: Path, skill_ref: str, profile: str | None = None,
                  model_override: str | None = None, effort_override: str | None = None,
                  config_path: Path | None = None,
                  environ: dict[str, str] | None = None) -> Route:
    root = root.resolve()
    target = target.resolve()
    config = load_config(root, config_path)
    plugin, skill = parse_skill_ref(skill_ref)
    tier, tier_source, skill_file = resolve_tier(root, plugin, skill, config.get("default_tier", "sonnet"))
    selected_profile, profile_source = resolve_profile(config, target, profile, environ)
    tier_route = config["profiles"][selected_profile].get(tier)
    if not isinstance(tier_route, dict):
        raise RoutingError(f"Profile {selected_profile} has no route for tier {tier!r}")
    model = model_override or tier_route["model"]
    effort = effort_override or tier_route["reasoning_effort"]
    if not isinstance(model, str) or not model:
        raise RoutingError("Resolved model is empty")
    if not isinstance(effort, str) or not effort:
        raise RoutingError("Resolved reasoning effort is empty")
    return Route(plugin=plugin, skill=skill, tier=tier, profile=selected_profile,
                 model=model, reasoning_effort=effort,
                 skill_file=str(skill_file), tier_source=tier_source,
                 profile_source=profile_source)


def child_prompt(root: Path, target: Path, route: Route, skill_args: list[str]) -> str:
    invocation = f"/{route.plugin}:{route.skill}"
    if skill_args:
        invocation += " " + shlex.join(skill_args)
    return "\n".join([
        "Execute exactly one AI Dev Loop skill in this child Codex run.",
        f"Invocation: {invocation}",
        f"Invocation arguments (exact JSON): {json.dumps(skill_args, ensure_ascii=False)}",
        f"Skill instructions: {route.skill_file}",
        f"AI Dev Loop repository root: {root.resolve()}",
        f"Target project root: {target.resolve()}",
        "Read the complete SKILL.md before acting. Resolve its @rules, @skills, templates, and tools references against the AI Dev Loop repository root.",
        "Work in the target project root and follow its AGENTS.md too. Preserve unrelated user changes.",
        "If this skill orchestrates child AI Dev Loop skills, use the AI Dev Loop model router for those children; never reroute this same invocation.",
        "Complete and verify the requested skill, then return a concise result with changed files and checks.",
    ])


def build_command(codex_binary: str, root: Path, target: Path, route: Route,
                  skill_args: list[str]) -> list[str]:
    return [
        codex_binary,
        "exec",
        "--model", route.model,
        "--config", f'model_reasoning_effort="{route.reasoning_effort}"',
        "--cd", str(target.resolve()),
        child_prompt(root, target, route, skill_args),
    ]


def command_display(command: list[str]) -> str:
    visible = list(command)
    if visible:
        visible[-1] = "<generated-skill-prompt>"
    return shlex.join(visible)
