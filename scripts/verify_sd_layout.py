#!/usr/bin/env python3
"""Validate a prepared /switch/gizmoduck directory before copying it to SD."""
from __future__ import annotations

import argparse
import struct
from pathlib import Path


def elf_is_aarch64(path: Path) -> bool:
    data = path.read_bytes()[:20]
    return len(data) == 20 and data[:4] == b"\x7fELF" and data[4] == 2 and struct.unpack_from("<H", data, 18)[0] == 183


def nro_has_control_assets(path: Path) -> bool:
    """Return true only for an NRO with a JPEG icon and NACP asset fields."""
    data = path.read_bytes()
    offset = data.rfind(b"ASET")
    # NRO AssetHeader: magic + version, then icon/nacp/romfs offset-size pairs.
    if offset < 0 or offset + 0x30 > len(data):
        return False
    icon_offset, icon_size, nacp_offset, nacp_size = struct.unpack_from("<QQQQ", data, offset + 8)
    icon_start = offset + icon_offset
    nacp_start = offset + nacp_offset
    return (icon_size > 4 and nacp_size > 0 and
            icon_start + icon_size <= len(data) and nacp_start + nacp_size <= len(data) and
            data[icon_start:icon_start + 3] == b"\xff\xd8\xff")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", type=Path)
    parser.add_argument("--expected-assets", type=int, default=3469)
    args = parser.parse_args()
    root = args.directory
    required = (root / "gizmoduck.nro", root / "libgodot_android.so",
                root / "libc++_shared.so", root / "save",
                root / "android_root" / "etc" / "fonts.xml",
                root / "android_root" / "fonts" / "NotoSansCJKkr-Regular.otf")
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise SystemExit("missing required paths:\n" + "\n".join(missing))
    nro_path = root / "gizmoduck.nro"
    nro = nro_path.read_bytes()[:0x14]
    if len(nro) < 0x14 or nro[0x10:0x14] != b"NRO0":
        raise SystemExit("gizmoduck.nro is not a valid NRO header")
    if not nro_has_control_assets(nro_path):
        raise SystemExit("gizmoduck.nro is missing its embedded icon or NACP metadata")
    for name in ("libgodot_android.so", "libc++_shared.so"):
        if not elf_is_aarch64(root / name):
            raise SystemExit(f"{name} is not a 64-bit AArch64 ELF")
    assets = root / "assets"
    pck = root / "game.pck"
    if assets.is_dir():
        if not (assets / "project.binary").is_file():
            raise SystemExit(f"missing required path: {assets / 'project.binary'}")
        count = sum(1 for path in assets.rglob("*") if path.is_file())
        if count != args.expected_assets:
            raise SystemExit(f"asset count is {count}, expected {args.expected_assets}")
        source = f"{count} assets"
    elif pck.is_file() and pck.stat().st_size > 0:
        source = f"PCK ({pck.stat().st_size} bytes)"
    else:
        raise SystemExit("missing game data: provide assets/project.binary or a non-empty game.pck")
    print(f"OK: {root} ({source}, ARM64 runtime)")


if __name__ == "__main__":
    main()
