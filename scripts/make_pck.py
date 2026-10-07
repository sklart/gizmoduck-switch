#!/usr/bin/env python3
"""Extract the original unencrypted PCK as one standalone game.pck file."""
from __future__ import annotations

import argparse
from pathlib import Path

from prepare_game import locate_pack


def make_pck(executable: Path, output: Path) -> int:
    blob = executable.read_bytes()
    start, size = locate_pack(blob)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(blob[start:start + size])
    return size


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("executable", type=Path)
    parser.add_argument("--output", type=Path, default=Path("game.pck"))
    args = parser.parse_args()
    size = make_pck(args.executable, args.output)
    print(f"wrote {args.output} ({size} bytes)")


if __name__ == "__main__":
    main()
