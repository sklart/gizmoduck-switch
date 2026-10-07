#!/usr/bin/env python3
"""Extract the unencrypted Godot 4 PCK appended to a Gizmoduck executable.

The output is Android-style assets/, deliberately outside version control.
"""
from __future__ import annotations

import argparse
import hashlib
import shutil
import struct
from pathlib import Path

MAGIC = b"GDPC"
PACK_DIR_ENCRYPTED = 1
PACK_FILE_ENCRYPTED = 1


def u32(blob: bytes, offset: int) -> int:
    return struct.unpack_from("<I", blob, offset)[0]


def u64(blob: bytes, offset: int) -> int:
    return struct.unpack_from("<Q", blob, offset)[0]


def locate_pack(blob: bytes) -> tuple[int, int]:
    if blob[-4:] != MAGIC:
        raise ValueError("not a Godot self-contained executable (missing GDPC footer)")
    pack_size = u64(blob, len(blob) - 12)
    start = len(blob) - pack_size - 12
    if start < 0 or blob[start : start + 4] != MAGIC:
        raise ValueError("invalid embedded PCK size or header")
    return start, pack_size


def extract(executable: Path, destination: Path) -> dict[str, object]:
    blob = executable.read_bytes()
    start, pack_size = locate_pack(blob)
    pack_format, major, minor, patch, flags = struct.unpack_from("<IIIII", blob, start + 4)
    if pack_format != 4:
        raise ValueError(f"unsupported PCK format {pack_format}; expected 4")
    if flags & PACK_DIR_ENCRYPTED:
        raise ValueError("PCK directory is encrypted; extraction needs the publisher's AES-256 key")
    file_base = start + u64(blob, start + 24)
    directory = start + u64(blob, start + 32)
    file_count = u32(blob, directory)
    cursor = directory + 4
    files: list[dict[str, object]] = []
    destination.mkdir(parents=True, exist_ok=True)
    for _ in range(file_count):
        name_length = u32(blob, cursor)
        cursor += 4
        raw_name = blob[cursor : cursor + name_length]
        cursor += name_length
        path_text = raw_name.rstrip(b"\0").decode("utf-8")
        # Godot accepts both canonical ``res://`` records and relative records
        # in an executable-embedded PCK.
        relative = Path(path_text.removeprefix("res://"))
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError(f"unsafe PCK path: {path_text!r}")
        offset, size = struct.unpack_from("<QQ", blob, cursor)
        cursor += 16
        digest = blob[cursor : cursor + 16]
        cursor += 16
        entry_flags = u32(blob, cursor)
        cursor += 4
        if entry_flags & PACK_FILE_ENCRYPTED:
            raise ValueError(f"encrypted PCK entry: {path_text}; extraction needs the publisher's AES-256 key")
        payload = blob[file_base + offset : file_base + offset + size]
        if len(payload) != size or hashlib.md5(payload).digest() != digest:
            raise ValueError(f"corrupt PCK entry: {path_text}")
        output = destination / relative
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(payload)
        files.append({"path": path_text, "size": size, "flags": entry_flags})
    return {"pck_start": start, "pck_size": pack_size, "format": pack_format,
            "godot": f"{major}.{minor}.{patch}", "flags": flags, "file_count": file_count,
            "files": files}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("executable", type=Path)
    parser.add_argument("--output", type=Path, default=Path("game/assets"))
    parser.add_argument("--clean", action="store_true")
    args = parser.parse_args()
    if args.clean and args.output.exists():
        shutil.rmtree(args.output)
    report = extract(args.executable, args.output)
    print("Godot", report["godot"], "PCK format", report["format"], "flags", hex(report["flags"]))
    print("extracted", report["file_count"], "files to", args.output)


if __name__ == "__main__":
    main()
