#!/usr/bin/env python3
"""Fetch and unpack the official Godot 4.7.2 ARM64 Android export runtime."""
from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import tempfile
import urllib.request
import zipfile
from pathlib import Path

DEFAULT_URL = ("https://github.com/godotengine/godot/releases/download/4.7.2-stable/"
               "godot-lib.4.7.2.stable.template_release.aar")
REQUIRED = ("jni/arm64-v8a/libgodot_android.so", "jni/arm64-v8a/libc++_shared.so")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--aar", type=Path, help="use an already downloaded official AAR")
    parser.add_argument("--output", type=Path, default=Path("runtime"))
    parser.add_argument("--sha256", help="expected SHA-256 from the official release")
    args = parser.parse_args()
    temporary: Path | None = None
    if args.aar:
        aar = args.aar
    else:
        handle, name = tempfile.mkstemp(suffix=".aar")
        os.close(handle)
        Path(name).unlink(missing_ok=True)
        temporary = Path(name)
        print("downloading", DEFAULT_URL)
        urllib.request.urlretrieve(DEFAULT_URL, temporary)
        aar = temporary
    try:
        actual = sha256(aar)
        if args.sha256 and actual.lower() != args.sha256.lower():
            raise SystemExit(f"SHA-256 mismatch for {aar}: {actual}")
        with zipfile.ZipFile(aar) as archive:
            missing = [name for name in REQUIRED if name not in archive.namelist()]
            if missing:
                raise SystemExit("not an official ARM64 Godot Android AAR: " + ", ".join(missing))
            args.output.mkdir(parents=True, exist_ok=True)
            for member in REQUIRED:
                destination = args.output / Path(member).name
                with archive.open(member) as source, destination.open("wb") as target:
                    shutil.copyfileobj(source, target)
                print(destination, sha256(destination))
    finally:
        if temporary:
            temporary.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
