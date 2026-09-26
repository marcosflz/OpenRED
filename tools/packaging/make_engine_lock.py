#!/usr/bin/env python3
"""Generate engine.lock: SHA-256 per file of the engine bundle inputs.

The lock covers ``engine/openred_engine/**`` (sidecar code and plugins) and
``engine/python/**`` (portable runtime + site-packages). Paths are POSIX and
relative to ``--root`` so the same file is valid inside the Tauri resource
directory (``<install>/engine/engine.lock``).

Deterministic: no timestamps, keys sorted; two runs over the same tree produce
byte-identical output. ``__pycache__``, ``*.pyc`` and download caches are
excluded.

Usage:
    uv run python tools/packaging/make_engine_lock.py
    uv run python tools/packaging/make_engine_lock.py --root engine --out engine/engine.lock
    uv run python tools/packaging/make_engine_lock.py --verify engine/engine.lock

Exit codes: 0 OK, 1 mismatch/verification failure, 2 usage error.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INCLUDE = ("openred_engine", "python")
EXCLUDE_DIRS = {"__pycache__", "_downloads", ".git"}
EXCLUDE_SUFFIXES = {".pyc", ".pyo", ".tmp"}


def iter_files(root: Path, include: tuple[str, ...]):
    for name in include:
        directory = root / name
        if not directory.is_dir():
            raise FileNotFoundError(f"missing bundle directory: {directory}")
        for path in sorted(directory.rglob("*")):
            if not path.is_file():
                continue
            if any(part in EXCLUDE_DIRS for part in path.relative_to(root).parts):
                continue
            if path.suffix in EXCLUDE_SUFFIXES:
                continue
            yield path


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_lock(root: Path, include: tuple[str, ...]) -> dict:
    files = {}
    for path in iter_files(root, include):
        relative = path.relative_to(root).as_posix()
        files[relative] = sha256_file(path)
    return {
        "format": 1,
        "algorithm": "sha256",
        "root": root.name,
        "includes": list(include),
        "file_count": len(files),
        "files": dict(sorted(files.items())),
    }


def dump_lock(lock: dict, out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="\n") as fh:
        json.dump(lock, fh, indent=2, ensure_ascii=False, sort_keys=False)
        fh.write("\n")


def verify_lock(lock: dict, root: Path) -> list[str]:
    problems = []
    files = lock.get("files", {})
    include = tuple(lock.get("includes", DEFAULT_INCLUDE))
    actual = {path.relative_to(root).as_posix(): sha256_file(path) for path in iter_files(root, include)}
    for name, digest in files.items():
        if name not in actual:
            problems.append(f"missing file: {name}")
        elif actual[name] != digest:
            problems.append(f"hash mismatch: {name}")
    for name in actual:
        if name not in files:
            problems.append(f"unexpected file: {name}")
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", default=str(REPO_ROOT / "engine"), help="engine tree holding the included dirs")
    parser.add_argument("--include", nargs="+", default=list(DEFAULT_INCLUDE), help="directories to hash (relative to root)")
    parser.add_argument("--out", default="", help="output lock path (default <root>/engine.lock)")
    parser.add_argument("--verify", default="", help="verify an existing lock against the tree instead of writing")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    include = tuple(args.include)
    if not root.is_dir():
        print(f"ERROR: root not found: {root}", file=sys.stderr)
        return 2

    if args.verify:
        lock_path = Path(args.verify)
        if not lock_path.is_file():
            print(f"ERROR: lock not found: {lock_path}", file=sys.stderr)
            return 2
        lock = json.loads(lock_path.read_text(encoding="utf-8"))
        problems = verify_lock(lock, root)
        if problems:
            print(f"FAIL: {len(problems)} difference(s)")
            for problem in problems[:50]:
                print(f"  - {problem}")
            return 1
        print(f"OK: {lock.get('file_count', len(lock.get('files', {})))} files verified against {root}")
        return 0

    try:
        lock = build_lock(root, include)
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        print("  The portable runtime is built by tools/python-portable/fetch_python.ps1|sh.", file=sys.stderr)
        return 2
    out = Path(args.out) if args.out else root / "engine.lock"
    dump_lock(lock, out)
    print(f"OK: wrote {out} ({lock['file_count']} files)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
