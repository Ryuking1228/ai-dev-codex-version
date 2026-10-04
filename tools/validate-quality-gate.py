#!/usr/bin/env python3
"""Validate AI Dev Loop's nine-stage quality-gate artifact.

The validator also re-runs Cloudflare's two zero-dependency artifact validators and verifies that
the vendored security-audit folder still matches skills-lock.json.
"""

from __future__ import annotations

import hashlib
import json
import os
import stat
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
LOCK_PATH = ROOT / "skills-lock.json"
SKILL_DIR = ROOT / ".agents" / "skills" / "security-audit"
STAGES = [
    "build",
    "unit",
    "contract",
    "integration",
    "sast",
    "dependency-scan",
    "api-security",
    "architecture-conformance",
    "independent-security-audit",
]
COMMAND_STAGES = set(STAGES[:6])
STATUSES = {"passed", "conditional", "failed", "blocked", "skipped"}
SKIP_REASONS = {"not-applicable", "not-configured", "skipped-by-user"}
SEVERITIES = ("critical", "high", "medium", "low", "informational")


def text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def integer(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def read_json(path: Path, label: str, errors: list[str]) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        errors.append(f"{label}: cannot read valid JSON: {exc}")
        return None


def folder_hash(root: Path) -> str:
    digest = hashlib.sha256()
    files = sorted(
        (
            path
            for path in root.rglob("*")
            if path.is_file() and ".git" not in path.parts and "node_modules" not in path.parts
        ),
        key=lambda path: path.relative_to(root).as_posix(),
    )
    for path in files:
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()


def validate_skill_lock(errors: list[str]) -> dict[str, Any] | None:
    lock = read_json(LOCK_PATH, "skills-lock.json", errors)
    if not isinstance(lock, dict):
        return None
    entry = (lock.get("skills") or {}).get("security-audit")
    if not isinstance(entry, dict):
        errors.append("skills-lock.json: missing security-audit entry")
        return None
    if entry.get("source") != "cloudflare/security-audit-skill":
        errors.append("skills-lock.json: security-audit source is not Cloudflare's repository")
    ref = entry.get("ref")
    if not text(ref) or len(ref) != 40 or any(ch not in "0123456789abcdef" for ch in ref):
        errors.append("skills-lock.json: security-audit ref must be a full lowercase commit SHA")
    expected = entry.get("computedHash")
    if not text(expected):
        errors.append("skills-lock.json: security-audit computedHash is missing")
    elif not SKILL_DIR.is_dir():
        errors.append(f"vendored skill directory is missing: {SKILL_DIR}")
    else:
        symlinks = [path for path in SKILL_DIR.rglob("*") if path.is_symlink()]
        if symlinks:
            errors.append("vendored security-audit folder must not contain symlinks")
        else:
            actual = folder_hash(SKILL_DIR)
            if actual != expected:
                errors.append(
                    "vendored security-audit folder does not match skills-lock.json: "
                    f"expected {expected}, got {actual}"
                )
    return entry


def resolve_artifact(raw: str, gate_path: Path) -> Path:
    path = Path(raw)
    return path if path.is_absolute() else (gate_path.parent / path).resolve()


def regular_file(path: Path) -> bool:
    try:
        return stat.S_ISREG(os.lstat(path).st_mode)
    except OSError:
        return False


def run_upstream_validator(script: str, artifact: Path, errors: list[str]) -> None:
    script_path = SKILL_DIR / script
    try:
        result = subprocess.run(
            ["node", str(script_path), str(artifact)],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        errors.append(f"stage independent-security-audit: could not run {script}: {exc}")
        return
    if result.returncode != 0:
        summary = result.stdout.strip().splitlines()
        detail = summary[-1] if summary else "no output"
        errors.append(f"stage independent-security-audit: {script} failed: {detail}")


def count_findings(records: Any) -> dict[str, Any] | None:
    if not isinstance(records, list):
        return None
    verdicts = Counter(record.get("verdict") for record in records if isinstance(record, dict))
    confirmed = Counter(
        record.get("severity", {}).get("overall_severity")
        for record in records
        if isinstance(record, dict) and record.get("verdict") == "confirmed"
    )
    return {
        "confirmed": {severity: confirmed[severity] for severity in SEVERITIES},
        "needs_validation": verdicts["needs_validation"],
        "rejected": verdicts["rejected"],
    }


def validate_stage9(
    stage: dict[str, Any], gate: dict[str, Any], gate_path: Path, lock: dict[str, Any] | None,
    errors: list[str],
) -> None:
    label = "stage independent-security-audit"
    status = stage.get("status")
    if stage.get("provider") != "cloudflare/security-audit-skill":
        errors.append(f"{label}: provider must be cloudflare/security-audit-skill")
    if lock and stage.get("skill_ref") != lock.get("ref"):
        errors.append(f"{label}: skill_ref must match the pinned skills-lock.json ref")
    if stage.get("source_ref") != gate.get("source_ref"):
        errors.append(f"{label}: source_ref must match the gate's source_ref")

    if status in {"blocked", "skipped"}:
        return

    if stage.get("profile") not in {"quick", "standard", "deep"}:
        errors.append(f"{label}: profile must be quick, standard, or deep")
    if stage.get("run_status") not in {"complete", "incomplete"}:
        errors.append(f"{label}: run_status must be complete or incomplete")
    scope_paths = stage.get("scope_paths")
    if not isinstance(scope_paths, list) or not scope_paths or not all(text(path) for path in scope_paths):
        errors.append(f"{label}: scope_paths must be a non-empty string array")

    artifacts = stage.get("artifacts")
    artifact_paths: dict[str, Path] = {}
    for key in ("run_metadata", "coverage_ledger", "findings", "report"):
        raw = artifacts.get(key) if isinstance(artifacts, dict) else None
        if not text(raw):
            errors.append(f"{label}: artifacts.{key} is required")
            continue
        path = resolve_artifact(raw, gate_path)
        artifact_paths[key] = path
        if not regular_file(path):
            errors.append(f"{label}: artifacts.{key} is not a regular file: {path}")

    validators = stage.get("validators")
    for key in ("coverage_ledger", "findings"):
        record = validators.get(key) if isinstance(validators, dict) else None
        if not isinstance(record, dict) or not text(record.get("command")):
            errors.append(f"{label}: validators.{key}.command is required")
        if not isinstance(record, dict) or not integer(record.get("exit_code")):
            errors.append(f"{label}: validators.{key}.exit_code must be an integer")
        elif status in {"passed", "conditional"} and record["exit_code"] != 0:
            errors.append(f"{label}: validators.{key} must exit 0 for {status}")

    metadata = None
    if "run_metadata" in artifact_paths and regular_file(artifact_paths["run_metadata"]):
        metadata = read_json(artifact_paths["run_metadata"], "run-metadata.json", errors)
    if isinstance(metadata, dict):
        for key in ("source_ref", "profile", "scope_paths", "run_status"):
            if metadata.get(key) != stage.get(key):
                errors.append(f"{label}: {key} does not match run-metadata.json")

    actual_counts = None
    if "findings" in artifact_paths and regular_file(artifact_paths["findings"]):
        actual_counts = count_findings(read_json(artifact_paths["findings"], "findings.json", errors))
    recorded_counts = stage.get("findings")
    if actual_counts is not None and isinstance(recorded_counts, dict):
        for key in ("confirmed", "needs_validation", "rejected"):
            if recorded_counts.get(key) != actual_counts[key]:
                errors.append(f"{label}: findings.{key} does not match findings.json")
    elif not isinstance(recorded_counts, dict):
        errors.append(f"{label}: findings summary is required")

    unvalidated = recorded_counts.get("unvalidated_candidates") if isinstance(recorded_counts, dict) else None
    if not integer(unvalidated) or unvalidated < 0:
        errors.append(f"{label}: findings.unvalidated_candidates must be a non-negative integer")

    if "coverage_ledger" in artifact_paths and regular_file(artifact_paths["coverage_ledger"]):
        run_upstream_validator("validate-coverage-ledger.cjs", artifact_paths["coverage_ledger"], errors)
    if "findings" in artifact_paths and regular_file(artifact_paths["findings"]):
        run_upstream_validator("validate-findings.cjs", artifact_paths["findings"], errors)

    confirmed = recorded_counts.get("confirmed", {}) if isinstance(recorded_counts, dict) else {}
    if status == "passed":
        if stage.get("run_status") != "complete":
            errors.append(f"{label}: a passed stage requires run_status complete")
        if any(confirmed.get(severity) != 0 for severity in ("critical", "high", "medium", "low")):
            errors.append(f"{label}: passed cannot contain confirmed critical/high/medium/low findings")
        if isinstance(recorded_counts, dict) and recorded_counts.get("needs_validation") != 0:
            errors.append(f"{label}: passed cannot contain needs_validation records")
        if unvalidated != 0:
            errors.append(f"{label}: passed cannot contain unvalidated candidates")
    elif status == "conditional":
        if stage.get("run_status") != "complete":
            errors.append(f"{label}: conditional requires run_status complete")
        if confirmed.get("critical", 0) or confirmed.get("high", 0) or unvalidated:
            errors.append(f"{label}: critical/high findings or unvalidated candidates require failed")
        if not (confirmed.get("medium", 0) or confirmed.get("low", 0) or
                (isinstance(recorded_counts, dict) and recorded_counts.get("needs_validation", 0))):
            errors.append(f"{label}: conditional requires a medium/low or needs_validation record")
        conditions = stage.get("conditions")
        if not isinstance(conditions, list) or not conditions:
            errors.append(f"{label}: conditional requires owner/decision conditions")
        else:
            for index, condition in enumerate(conditions):
                if (
                    not isinstance(condition, dict)
                    or not text(condition.get("fingerprint"))
                    or not text(condition.get("owner"))
                    or not text(condition.get("decision"))
                ):
                    errors.append(f"{label}: conditions[{index}] requires fingerprint, owner, and decision")


def derive_verdict(stages: list[dict[str, Any]]) -> str:
    if any(stage.get("status") in {"failed", "blocked"} for stage in stages):
        return "FAIL"
    for index, stage in enumerate(stages):
        if index < 4 and stage.get("status") == "skipped" and stage.get("reason") != "not-applicable":
            return "FAIL"
    if any(stage.get("status") == "conditional" for stage in stages):
        return "CONDITIONAL"
    if any(stage.get("status") == "skipped" and stage.get("reason") != "not-applicable" for stage in stages):
        return "CONDITIONAL"
    return "PASS"


def validate(gate_path: Path) -> list[str]:
    errors: list[str] = []
    lock = validate_skill_lock(errors)
    gate = read_json(gate_path, str(gate_path), errors)
    if not isinstance(gate, dict):
        return errors
    if gate.get("schema_version") != 2:
        errors.append("quality gate: schema_version must be 2")
    if not text(gate.get("source_ref")):
        errors.append("quality gate: source_ref is required")
    if gate.get("verdict") not in {"PASS", "CONDITIONAL", "FAIL"}:
        errors.append("quality gate: verdict must be PASS, CONDITIONAL, or FAIL")
    blocking = gate.get("blocking")
    if not isinstance(blocking, list) or not all(text(item) for item in blocking):
        errors.append("quality gate: blocking must be a string array")

    stages = gate.get("stages")
    if not isinstance(stages, list):
        errors.append("quality gate: stages must be an array")
        return errors
    names = [stage.get("stage") if isinstance(stage, dict) else None for stage in stages]
    if names != STAGES:
        errors.append(f"quality gate: stages must appear exactly in order: {', '.join(STAGES)}")
        return errors

    for stage in stages:
        name = stage["stage"]
        status_value = stage.get("status")
        if status_value not in STATUSES:
            errors.append(f"stage {name}: invalid status {status_value!r}")
            continue
        if status_value == "skipped" and stage.get("reason") not in SKIP_REASONS:
            errors.append(f"stage {name}: skipped requires an allowed reason")
        if status_value == "skipped" and stage.get("reason") == "skipped-by-user" and not (
            text(stage.get("waived_by")) and text(stage.get("detail"))
        ):
            errors.append(f"stage {name}: skipped-by-user requires waived_by and detail")
        if (
            name == "independent-security-audit"
            and status_value == "skipped"
            and stage.get("reason") == "not-configured"
        ):
            errors.append("stage independent-security-audit: not-configured is invalid; record an incomplete failure")
        if status_value == "blocked" and not (
            name == "independent-security-audit" and stage.get("reason") == "blocked-by-prior-stage"
        ):
            errors.append(f"stage {name}: blocked is only valid for stage 9 after a prior failure")
        if name in COMMAND_STAGES and status_value not in {"skipped", "blocked"}:
            if not text(stage.get("command")):
                errors.append(f"stage {name}: command is required")
            if not integer(stage.get("exit_code")):
                errors.append(f"stage {name}: exit_code must be an integer")
        if name == "independent-security-audit":
            validate_stage9(stage, gate, gate_path, lock, errors)

    if stages[-1].get("status") == "blocked" and not any(
        stage.get("status") == "failed" for stage in stages[:-1]
    ):
        errors.append("stage independent-security-audit: blocked-by-prior-stage requires a failed prior stage")

    derived = derive_verdict(stages)
    if gate.get("verdict") != derived:
        errors.append(f"quality gate: verdict must be {derived} for the recorded stage statuses")
    if derived != "PASS" and isinstance(blocking, list) and not blocking:
        errors.append("quality gate: a non-PASS verdict requires at least one blocking entry")
    return errors


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: validate-quality-gate.py <quality-gate.json>", file=sys.stderr)
        return 2
    gate_path = Path(argv[1]).resolve()
    errors = validate(gate_path)
    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print(f"PASS: valid nine-stage quality gate: {gate_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
