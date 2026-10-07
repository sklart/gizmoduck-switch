#!/usr/bin/env python3
"""Create a minimal SD-root patch between two extracted Gizmoduck releases."""
from __future__ import annotations

import argparse
import hashlib
import shutil
from pathlib import Path


def digest(path: Path) -> bytes:
    return hashlib.sha256(path.read_bytes()).digest()


def files(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): digest(path)
        for path in root.rglob("*") if path.is_file()
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--old-assets", type=Path, required=True)
    parser.add_argument("--new-assets", type=Path, required=True)
    parser.add_argument("--prepared-game", type=Path, required=True,
                        help="fully packaged 1.1.6 gizmoduck directory")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    old, new = files(args.old_assets), files(args.new_assets)
    changed = sorted(path for path in new if path not in old or new[path] != old[path])
    if set(old) - set(new):
        raise SystemExit("a patch cannot remove game files; make a full package instead")
    prepared = args.prepared_game.resolve()
    if not (prepared / "gizmoduck.nro").is_file():
        raise SystemExit(f"missing prepared game: {prepared}")
    root = args.output.resolve()
    if root.exists():
        shutil.rmtree(root)
    game = root / "switch" / "gizmoduck"
    (game / "assets").mkdir(parents=True)
    shutil.copy2(prepared / "gizmoduck.nro", game / "gizmoduck.nro")
    for relative in changed:
        source = prepared / "assets" / relative
        target = game / "assets" / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    # The Switch-specific CRT fix is intentionally outside the upstream diff.
    crt = Path("assets/shaders/crt.gdshader")
    target = game / "assets" / crt
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(prepared / "assets" / crt, target)
    (root / "PATCH-INSTRUCTIONS.txt").write_text(
        "Extract this archive to the root of the SD card and allow overwriting files.\n"
        "It updates a complete Gizmoduck Switch 1.1.2 installation to 1.1.6.\n"
        "Do not remove libgodot_android.so, libc++_shared.so, android_root, save, or other assets.\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"changed upstream assets: {len(changed)}")
    print(root)


if __name__ == "__main__":
    main()
