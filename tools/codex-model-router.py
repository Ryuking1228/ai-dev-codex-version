#!/usr/bin/env python3
"""Resolve and run AI Dev Loop skills with a cost-aware Codex model."""

from __future__ import annotations

from pathlib import Path
import argparse
import json
import os
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from lib.codex_model_router import (  # noqa: E402
    RoutingError,
    build_command,
    command_display,
    load_config,
    resolve_route,
)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("action", choices=("resolve", "run", "matrix"))
    result.add_argument("skill", nargs="?", help="Skill reference, e.g. architect:design-api")
    result.add_argument("--target", default=".", help="Target project root (default: current directory)")
    result.add_argument("--profile", choices=("economy", "balanced", "quality"))
    result.add_argument("--model", help="Override the routed model for this run")
    result.add_argument("--reasoning-effort", help="Override the routed reasoning effort")
    result.add_argument("--config", type=Path, help="Alternate routing JSON (mainly for tests)")
    result.add_argument("--codex-bin", help="Codex executable; defaults to CODEX_BIN or PATH")
    result.add_argument("--dry-run", action="store_true", help="Print the child command without running it")
    return result


def parse_args(argv: list[str] | None = None) -> tuple[argparse.Namespace, list[str]]:
    values = list(sys.argv[1:] if argv is None else argv)
    if "--" in values:
        split = values.index("--")
        router_args, skill_args = values[:split], values[split + 1:]
    else:
        router_args, skill_args = values, []
    return parser().parse_args(router_args), skill_args


def main(argv: list[str] | None = None) -> int:
    args, skill_args = parse_args(argv)
    target = Path(args.target).resolve()
    try:
        if args.action == "matrix":
            config = load_config(ROOT, args.config)
            selected = args.profile or config["default_profile"]
            print(json.dumps({"profile": selected, "routes": config["profiles"][selected]},
                             ensure_ascii=False, indent=2))
            return 0
        if not args.skill:
            raise RoutingError(f"{args.action} requires <plugin>:<skill>")
        route = resolve_route(ROOT, target, args.skill, args.profile, args.model,
                              args.reasoning_effort, args.config)
        if args.action == "resolve":
            print(json.dumps(route.to_dict(), ensure_ascii=False, indent=2))
            return 0
        codex_binary = args.codex_bin or os.environ.get("CODEX_BIN") or shutil.which("codex")
        if not codex_binary:
            raise RoutingError("Codex CLI was not found; set CODEX_BIN or add codex to PATH")
        command = build_command(codex_binary, ROOT, target, route, skill_args)
        print(json.dumps({"route": route.to_dict(), "command": command_display(command)},
                         ensure_ascii=False), file=sys.stderr)
        if args.dry_run:
            print(json.dumps({"route": route.to_dict(), "command": command},
                             ensure_ascii=False, indent=2))
            return 0
        return subprocess.run(command, check=False).returncode
    except RoutingError as exc:
        print(f"codex-model-router: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
