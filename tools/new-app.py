#!/usr/bin/env python3
"""Create a maintained Codex app outside Nexus's disposable generated/ tree."""
import argparse
import re
import shutil
from pathlib import Path


def create(target: Path, name: str):
    if not re.fullmatch(r"[a-z][a-z0-9-]{1,62}", name):
        raise ValueError("Use a lowercase kebab-case app name (2–63 characters)")
    target = target.resolve()
    if target.exists():
        raise ValueError("Destination already exists; no files were overwritten")
    source = Path(__file__).resolve().parents[1] / "templates" / "codex-postgres-app"
    shutil.copytree(source, target, ignore=shutil.ignore_patterns(
        "__pycache__", "*.pyc", "node_modules", "dist", ".pytest_cache", ".app-state",
        "test-results", "playwright-report", ".env"))
    for path in target.rglob("*"):
        if path.is_file():
            path.write_text(path.read_text().replace("__APP_NAME__", name))
    shutil.copy2(source.parents[1] / "LICENSE", target / "LICENSE")
    print(f"Created {target}\nNext: cd {target} && python3 appctl.py up")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", type=Path)
    parser.add_argument("--name", required=True)
    args = parser.parse_args()
    try:
        create(args.target, args.name)
    except ValueError as exc:
        parser.exit(2, str(exc) + "\n")
