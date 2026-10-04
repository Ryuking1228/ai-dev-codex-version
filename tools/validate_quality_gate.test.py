#!/usr/bin/env python3
"""Executable contracts for the nine-stage quality-gate validator."""

from __future__ import annotations

import copy
import json
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "tools" / "validate-quality-gate.py"
SKILL_REF = json.loads((ROOT / "skills-lock.json").read_text())["skills"]["security-audit"]["ref"]
NAMES = [
    "build", "unit", "contract", "integration", "sast", "dependency-scan",
    "api-security", "architecture-conformance", "independent-security-audit",
]


def stage9(run: Path) -> dict:
    return {
        "stage": "independent-security-audit",
        "status": "passed",
        "provider": "cloudflare/security-audit-skill",
        "skill_ref": SKILL_REF,
        "source_ref": "abc123-clean",
        "profile": "quick",
        "scope_paths": ["src/order"],
        "run_status": "complete",
        "artifacts": {
            "run_metadata": str(run / "run-metadata.json"),
            "coverage_ledger": str(run / "coverage-ledger.json"),
            "findings": str(run / "findings.json"),
            "report": str(run / "REPORT.md"),
        },
        "validators": {
            "coverage_ledger": {"command": "node validate-coverage-ledger.cjs", "exit_code": 0},
            "findings": {"command": "node validate-findings.cjs", "exit_code": 0},
        },
        "findings": {
            "confirmed": {name: 0 for name in ("critical", "high", "medium", "low", "informational")},
            "needs_validation": 0,
            "rejected": 0,
            "unvalidated_candidates": 0,
        },
    }


def fixture(root: Path) -> dict:
    run = root / "audit"
    run.mkdir()
    (run / "run-metadata.json").write_text(json.dumps({
        "source_ref": "abc123-clean",
        "profile": "quick",
        "scope_paths": ["src/order"],
        "run_status": "complete",
    }))
    (run / "coverage-ledger.json").write_text("[]\n")
    (run / "findings.json").write_text("[]\n")
    (run / "REPORT.md").write_text("# Security audit\n")
    stages = []
    for name in NAMES[:6]:
        stages.append({"stage": name, "status": "passed", "command": f"run-{name}", "exit_code": 0})
    stages.extend([
        {"stage": "api-security", "status": "passed", "findings": {"critical": 0, "major": 0}},
        {"stage": "architecture-conformance", "status": "passed", "findings": {"critical": 0}},
        stage9(run),
    ])
    return {
        "schema_version": 2,
        "run_at": "2026-10-05T00:00:00Z",
        "source_ref": "abc123-clean",
        "source_root": "src",
        "verdict": "PASS",
        "stages": stages,
        "blocking": [],
    }


def run_validator(gate: dict, root: Path) -> subprocess.CompletedProcess[str]:
    path = root / "quality-gate.json"
    path.write_text(json.dumps(gate))
    return subprocess.run(
        ["python3", str(VALIDATOR), str(path)], text=True,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False,
    )


def check(label: str, condition: bool, detail: str = "") -> None:
    if not condition:
        raise AssertionError(f"{label}: {detail}")
    print(f"ok - {label}")


def needs_validation_record() -> dict:
    source = {
        "kind": "entrypoint",
        "file": "src/parser.c",
        "line": 10,
        "scope": "parse_size",
        "description": "The parser forwards the declared size to the allocation path.",
    }
    evidence = {
        "file": "src/parser.c",
        "line": 10,
        "description": "The generated allocation bound is absent from this checkout.",
    }
    return {
        "verdict": "needs_validation",
        "fingerprint": "src-parser-size-hypothesis",
        "title": "Unchecked parsed size",
        "description": "A parsed size may reach an allocation without a limit.",
        "claimed_root_cause": "parse_size may pass an unbounded value to allocate.",
        "trace": [source],
        "evidence": [evidence],
        "blockers": ["The generated parser source is absent from this checkout."],
        "validation_plan": {
            "local": "Generate the parser and submit the smallest input above the documented limit.",
        },
    }


with tempfile.TemporaryDirectory(prefix="quality-gate-test-") as tmp:
    root = Path(tmp)
    valid = fixture(root)
    result = run_validator(valid, root)
    check("accepts a complete passing nine-stage gate", result.returncode == 0, result.stdout)

    conditional_root = root / "conditional"
    conditional_root.mkdir()
    conditional = fixture(conditional_root)
    conditional_record = needs_validation_record()
    findings_path = Path(conditional["stages"][-1]["artifacts"]["findings"])
    findings_path.write_text(json.dumps([conditional_record]))
    conditional["stages"][-1]["status"] = "conditional"
    conditional["stages"][-1]["findings"]["needs_validation"] = 1
    conditional["stages"][-1]["conditions"] = [{
        "fingerprint": conditional_record["fingerprint"],
        "owner": "security-owner",
        "decision": "Generate the parser and run the bounded local validation plan.",
    }]
    conditional["verdict"] = "CONDITIONAL"
    conditional["blocking"] = [conditional_record["fingerprint"]]
    result = run_validator(conditional, conditional_root)
    check("accepts unresolved evidence only as an owned conditional", result.returncode == 0, result.stdout)

    missing = copy.deepcopy(valid)
    missing["stages"].pop()
    result = run_validator(missing, root)
    check("rejects a missing independent gate", result.returncode == 1 and "exactly in order" in result.stdout, result.stdout)

    wrong_ref = copy.deepcopy(valid)
    wrong_ref["stages"][-1]["skill_ref"] = "0" * 40
    result = run_validator(wrong_ref, root)
    check("rejects an unpinned third-party skill ref", result.returncode == 1 and "skill_ref" in result.stdout, result.stdout)

    unresolved = copy.deepcopy(valid)
    unresolved["stages"][-1]["findings"]["needs_validation"] = 1
    result = run_validator(unresolved, root)
    check("rejects a false pass with unresolved validation", result.returncode == 1 and "findings.needs_validation" in result.stdout, result.stdout)

    blocked = copy.deepcopy(valid)
    blocked["stages"][0]["status"] = "failed"
    blocked["stages"][0]["exit_code"] = 1
    blocked["stages"][-1] = {
        "stage": "independent-security-audit",
        "status": "blocked",
        "reason": "blocked-by-prior-stage",
        "provider": "cloudflare/security-audit-skill",
        "skill_ref": SKILL_REF,
        "source_ref": "abc123-clean",
    }
    blocked["verdict"] = "FAIL"
    blocked["blocking"] = ["build"]
    result = run_validator(blocked, root)
    check("accepts an explicit fail-fast block before stage 9", result.returncode == 0, result.stdout)

    missing_runtime = copy.deepcopy(valid)
    missing_runtime["stages"][-1] = {
        "stage": "independent-security-audit",
        "status": "skipped",
        "reason": "not-configured",
        "provider": "cloudflare/security-audit-skill",
        "skill_ref": SKILL_REF,
        "source_ref": "abc123-clean",
    }
    missing_runtime["verdict"] = "CONDITIONAL"
    missing_runtime["blocking"] = ["independent-security-audit"]
    result = run_validator(missing_runtime, root)
    check("fails closed when the independent runtime is unavailable", result.returncode == 1 and "not-configured is invalid" in result.stdout, result.stdout)

print("all quality-gate validator contracts passed")
