#!/usr/bin/env python3
"""Build a PCK variant whose project setting stretches Gizmoduck to 16:9."""
from __future__ import annotations

import argparse
import hashlib
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from package_sd import add_project_string_setting

PCK_MAGIC = b"GDPC"
PCK_HEADER_SIZE = 112
ASPECT_KEY = b"display/window/stretch/aspect"
# Godot's `ignore` aspect mode scales each axis to the window dimensions.
ASPECT_VALUE = b"ignore"


def entries(pck: bytes) -> tuple[int, int, list[tuple[str, int, int, int, int]]]:
    """Return file-base, directory offset and mutable-field locations."""
    if pck[:4] != PCK_MAGIC:
        raise ValueError("not a Godot PCK")
    file_base = struct.unpack_from("<Q", pck, 24)[0]
    directory = struct.unpack_from("<Q", pck, 32)[0]
    if file_base < PCK_HEADER_SIZE or directory > len(pck):
        raise ValueError("invalid PCK offsets")
    count = struct.unpack_from("<I", pck, directory)[0]
    cursor = directory + 4
    result = []
    for _ in range(count):
        length = struct.unpack_from("<I", pck, cursor)[0]
        cursor += 4
        name = pck[cursor:cursor + length].rstrip(b"\0").decode("utf-8")
        cursor += length
        fields = cursor
        offset, size = struct.unpack_from("<QQ", pck, fields)
        cursor += 16 + 16 + 4  # offset/size, MD5, flags
        result.append((name, fields, offset, size, cursor))
    # Godot 4.7.2 exports ended exactly at the directory in 1.1.12, while
    # 1.1.13 adds four zero padding bytes after it. Keep that harmless trailer
    # in the rewritten PCK instead of mistaking it for malformed metadata.
    trailer = pck[cursor:]
    if trailer not in (b"", b"\0\0\0\0"):
        raise ValueError("unexpected PCK directory trailer")
    return file_base, directory, result


def stretched_pck(source: Path, output: Path) -> None:
    pck = source.read_bytes()
    file_base, directory, records = entries(pck)
    target = next((record for record in records if record[0] == "project.binary"), None)
    if target is None:
        raise ValueError("PCK has no project.binary")
    _, fields, offset, size, _ = target
    project = bytearray(pck[file_base + offset:file_base + offset + size])
    if len(project) != size:
        raise ValueError("truncated project.binary")

    # `project.binary` is an ECFG table. Appending a later value is how Godot
    # represents an override, without assuming the length of the upstream
    # setting (which is currently `keep`, shorter than `ignore`).
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".project.tmp")
    temporary.write_bytes(project)
    try:
        add_project_string_setting(temporary, ASPECT_KEY, ASPECT_VALUE)
        replacement = temporary.read_bytes()
    finally:
        temporary.unlink(missing_ok=True)

    # Preserve all upstream payload bytes and append the changed project just
    # before a rewritten directory. The PCK directory points at this new copy;
    # the old project and directory become harmless unused data.
    rebuilt = bytearray(pck[:directory])
    rebuilt += b"\0" * ((-len(rebuilt)) % 16)
    replacement_offset = len(rebuilt) - file_base
    rebuilt += replacement
    new_directory = bytearray(pck[directory:])
    relative = fields - directory
    struct.pack_into("<QQ", new_directory, relative, replacement_offset, len(replacement))
    new_directory[relative + 16:relative + 32] = hashlib.md5(replacement).digest()
    directory_offset = len(rebuilt)
    rebuilt += new_directory
    struct.pack_into("<Q", rebuilt, 32, directory_offset)
    output.write_bytes(rebuilt)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path, help="original standalone game.pck")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    stretched_pck(args.source, args.output)
    print(f"wrote {args.output} ({args.output.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
