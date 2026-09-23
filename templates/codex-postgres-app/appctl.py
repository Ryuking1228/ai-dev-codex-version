#!/usr/bin/env python3
"""Local app lifecycle. Verification is bound to a source fingerprint, not a claim."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import subprocess
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
STATE = ROOT / ".app-state"
IGNORED = {".git", ".venv", "node_modules", "dist", "__pycache__", ".pytest_cache",
           ".app-state", "test-results", "playwright-report"}


def fingerprint(root=ROOT):
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if not path.is_file() or path.is_symlink() or any(p in IGNORED for p in relative.parts):
            continue
        if path.name.startswith(".env") or path.suffix == ".pyc":
            continue
        digest.update(str(relative).encode() + b"\0" + path.read_bytes() + b"\0")
    return digest.hexdigest()


def record(name, value):
    STATE.mkdir(exist_ok=True)
    temporary = STATE / (name + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2))
    temporary.replace(STATE / name)


def run(command, *, capture=False):
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=capture)
    if result.returncode:
        raise RuntimeError(f"Command failed (exit {result.returncode}): {command[0]}")
    return result.stdout if capture else None


def compose(*args):
    return run(["docker", "compose", "--profile", "test", *args])


def initialize():
    STATE.mkdir(exist_ok=True)
    if not (ROOT / ".env").exists():
        with open(ROOT / ".env", "x", opener=lambda p, flags: os.open(p, flags, 0o600)) as handle:
            handle.write("POSTGRES_PASSWORD=" + secrets.token_hex(24) + "\n")


def up():
    initialize()
    compose("up", "-d", "--build", "--wait", "--wait-timeout", "180", "app")
    print("Open http://localhost:8000 on the machine running Docker.")


def health(url):
    with urllib.request.urlopen(url, timeout=15) as response:
        if response.status != 200 or json.load(response).get("status") != "ok":
            raise RuntimeError("Health check failed")


def junit_count(path):
    root = ET.parse(path).getroot()
    suites = [root] if root.tag == "testsuite" else list(root.iter("testsuite"))
    total = sum(int(s.get("tests", 0)) for s in suites)
    bad = sum(int(s.get(key, 0)) for s in suites for key in ("failures", "errors", "skipped"))
    if total == 0 or bad:
        raise RuntimeError("Backend tests were empty, failed, or skipped")
    return total


def verify():
    initialize()
    result = {"source": fingerprint(), "at": time.time(), "passed": False, "stages": []}
    record("verification.json", result)  # Invalidate any earlier successful run immediately.
    try:
        up()  # Dockerfile builds/types-checks the real frontend.
        result["stages"].append({"name": "build", "passed": True})
        health("http://127.0.0.1:8000/api/health")
        result["stages"].append({"name": "database-health", "passed": True})
        for filename in ("backend-results.xml", "e2e-results.json"):
            (STATE / filename).unlink(missing_ok=True)
        compose("run", "--rm", "backend-tests")
        result["stages"].append({"name": "backend", "passed": True,
                                  "tests": junit_count(STATE / "backend-results.xml")})
        compose("run", "--rm", "browser-tests")
        stats = json.loads((STATE / "e2e-results.json").read_text())["stats"]
        if stats.get("expected", 0) < 1 or any(stats.get(key, 0) for key in ("unexpected", "flaky", "skipped")):
            raise RuntimeError("Browser tests were empty, failed, flaky, or skipped")
        result["stages"].append({"name": "browser", "passed": True, "tests": stats["expected"]})
        if result["source"] != fingerprint():
            raise RuntimeError("Source changed during verification; run verify again")
        result["passed"] = True
    finally:
        record("verification.json", result)
    print("Verification passed for source " + result["source"][:12])


def release_check():
    result = json.loads((STATE / "verification.json").read_text())
    if not result.get("passed") or result.get("source") != fingerprint():
        raise RuntimeError("No passing verification for this source. Run verify again.")
    inspected = json.loads((STATE / "inspection.json").read_text())
    if inspected.get("source") != fingerprint() or not inspected.get("note", "").strip():
        raise RuntimeError("Inspect the current UI and record the result with inspect --note.")
    print("Current source has passing automated verification and a recorded UI inspection.")


def deploy():
    release_check()
    config = json.loads((ROOT / "app-workflow.json").read_text())["deploy"]
    command, url = config.get("command"), config.get("health_url")
    if not config.get("environment") or not isinstance(command, list) or not command or not all(isinstance(x, str) for x in command):
        raise RuntimeError("Set an explicit deployment environment and command array first")
    if not isinstance(url, str) or not url.startswith("https://"):
        raise RuntimeError("Set the deployment HTTPS health URL first")
    result = {"source": fingerprint(), "environment": config["environment"],
              "health_url": url, "at": time.time(), "passed": False}
    record("deployment.json", result)
    run(command)
    health(url)
    if result["source"] != fingerprint():
        raise RuntimeError("Source changed during deployment; verify the deployed revision")
    result["passed"] = True
    record("deployment.json", result)
    print("Deployment command succeeded and health responded successfully.")


def push(repo):
    owner = json.loads((ROOT / "app-workflow.json").read_text())["github_owner"]
    if not re.fullmatch(re.escape(owner) + r"/[A-Za-z0-9_.-]+", repo or ""):
        raise RuntimeError(f"Use an existing private repository under {owner}")
    info = json.loads(run(["gh", "repo", "view", repo, "--json", "visibility,nameWithOwner"], capture=True))
    if info.get("visibility") != "PRIVATE" or info.get("nameWithOwner", "").lower() != repo.lower():
        raise RuntimeError("Destination must be the requested PRIVATE repository")
    if run(["git", "status", "--porcelain"], capture=True).strip():
        raise RuntimeError("Review and commit changes before pushing")
    tracked = run(["git", "ls-files"], capture=True).splitlines()
    if any(any(part.startswith(".env") and part != ".env.example" or part in {".app-state", ".venv", "node_modules"}
               for part in Path(p).parts) for p in tracked):
        raise RuntimeError("Local credentials or runtime artifacts are tracked; remove them before pushing")
    run(["git", "push", "https://github.com/" + repo + ".git", "HEAD:main"])
    print("Pushed to https://github.com/" + repo)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["up", "down", "verify", "inspect", "release-check", "deploy", "push", "status"])
    parser.add_argument("--note")
    parser.add_argument("--repo")
    args = parser.parse_args()
    if args.action == "up": up()
    elif args.action == "down": compose("down")  # Never removes named data volumes.
    elif args.action == "verify": verify()
    elif args.action == "inspect":
        if not args.note or not args.note.strip():
            raise RuntimeError("Describe the actual UI workflow inspected with --note")
        record("inspection.json", {"source": fingerprint(), "note": args.note, "at": time.time()})
    elif args.action == "release-check": release_check()
    elif args.action == "deploy": deploy()
    elif args.action == "push": push(args.repo)
    else:
        for name in ("verification.json", "inspection.json", "deployment.json"):
            path = STATE / name
            if path.exists():
                data = json.loads(path.read_text())
                print(name, "current" if data.get("source") == fingerprint() else "STALE", json.dumps(data, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, OSError, ValueError, KeyError) as exc:
        print("Stopped: " + str(exc), file=sys.stderr)
        sys.exit(1)
