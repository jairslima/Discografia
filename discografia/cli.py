from __future__ import annotations

import argparse
from pathlib import Path

from .core import process_run, process_signal, process_status


def resolve_root(args_root: str | None) -> Path:
    if args_root:
        return Path(args_root).expanduser().resolve()
    return Path.cwd().resolve()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Automacao de discografia com pausa e retomada.")
    parser.add_argument("command", nargs="?", default="run", choices=["run", "resume", "pause", "cancel", "status"])
    parser.add_argument("root", nargs="?")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    root = resolve_root(args.root)
    root.mkdir(parents=True, exist_ok=True)

    if args.command == "run":
        return process_run(root, resume=False)
    if args.command == "resume":
        return process_run(root, resume=True)
    if args.command == "pause":
        return process_signal(root, "pause")
    if args.command == "cancel":
        return process_signal(root, "cancel")
    if args.command == "status":
        return process_status(root)
    return 1
