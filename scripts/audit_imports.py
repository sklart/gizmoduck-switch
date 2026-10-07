#!/usr/bin/env python3
"""Compare the runtime's undefined ELF symbols with the wrapper import table."""
from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path


def undef_symbols(readelf: str, library: Path) -> set[str]:
    result = subprocess.run([readelf, "-Ws", str(library)], check=True, text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    symbols = set()
    for line in result.stdout.splitlines():
        if " UND " not in line:
            continue
        match = re.search(r"\bUND\s+([^\s@]+)(?:@[^\s]+)?", line)
        if match:
            symbols.add(match.group(1))
    return symbols


def wrapper_symbols(source: Path) -> set[str]:
    text = (source / "imports.c").read_text(encoding="utf-8")
    text += (source / "gl_imports.inc").read_text(encoding="utf-8")
    return set(re.findall(r'\{\s*"([^"]+)"', text))


def exported_symbols(readelf: str, library: Path) -> set[str]:
    result = subprocess.run([readelf, "-Ws", str(library)], check=True, text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    symbols = set()
    for line in result.stdout.splitlines():
        match = re.search(r"\b(?:GLOBAL|WEAK)\s+DEFAULT\s+\d+\s+([^\s@]+)", line)
        if match:
            symbols.add(match.group(1))
    return symbols


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("library", type=Path)
    parser.add_argument("--source", type=Path, default=Path("source"))
    parser.add_argument("--readelf", default="readelf")
    parser.add_argument("--provider", type=Path, action="append", default=[],
                        help="ELF loaded before the target (for example libc++_shared.so)")
    args = parser.parse_args()
    undefined = undef_symbols(args.readelf, args.library)
    provided = wrapper_symbols(args.source)
    # C++ ABI symbols are deliberately resolved from libc++_shared.so after it
    # is loaded first; weak TLS and zstd trace hooks need no implementation.
    ignored = lambda name: name.startswith(("_Z", "_ITM", "ZSTD_"))
    providers = set().union(*(exported_symbols(args.readelf, path) for path in args.provider))
    missing = sorted(name for name in undefined - provided - providers if not ignored(name))
    print(f"undefined: {len(undefined)}")
    print(f"mapped directly: {len(undefined) - len(missing)}")
    print(f"resolved by providers: {len(undefined & providers)}")
    print(f"non-C++/non-weak missing: {len(missing)}")
    print("\n".join(missing))
    raise SystemExit(bool(missing))


if __name__ == "__main__":
    main()
