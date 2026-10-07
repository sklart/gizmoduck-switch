#!/usr/bin/env python3
"""Prepare a complete local Gizmoduck Switch SD-card directory from a legal ZIP or EXE.

No game data, runtime, font, icon, PCK, or generated SD-card files are kept in
the repository.  This helper obtains them locally from a user-supplied official ZIP
or already extracted EXE and
official upstream downloads, then invokes the existing packager.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FONT_NAME = "NotoSansCJKkr-Regular.otf"
DEFAULT_FONT_URL = (
    "https://github.com/notofonts/noto-cjk/raw/main/"
    "Sans/OTF/Korean/NotoSansCJKkr-Regular.otf"
)


def run(command: list[str]) -> None:
    print("+", " ".join(command))
    subprocess.run(command, cwd=ROOT, check=True)


def download_font(destination: Path, url: str) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    print("downloading", url)
    with urllib.request.urlopen(url) as source, destination.open("wb") as target:
        shutil.copyfileobj(source, target)
    if destination.stat().st_size == 0:
        raise RuntimeError(f"downloaded font is empty: {destination}")


def powershell() -> str:
    for name in ("pwsh", "powershell"):
        candidate = shutil.which(name)
        if candidate:
            return candidate
    raise RuntimeError("PowerShell was not found; install PowerShell to extract the NRO icon")


def source_executable(source: Path, work: Path) -> Path:
    """Return an EXE directly, or extract exactly one Gizmoduck.exe from a ZIP."""
    if source.suffix.lower() != ".zip":
        return source

    try:
        with zipfile.ZipFile(source) as archive:
            candidates = [
                entry for entry in archive.infolist()
                if not entry.is_dir() and Path(entry.filename).name.lower() == "gizmoduck.exe"
            ]
            if len(candidates) != 1:
                names = ", ".join(entry.filename for entry in candidates) or "none"
                raise ValueError(
                    "archive must contain exactly one Gizmoduck.exe "
                    f"(found: {names})"
                )
            extracted = work / "source" / "Gizmoduck.exe"
            extracted.parent.mkdir(parents=True, exist_ok=True)
            print("extracting", candidates[0].filename, "from", source)
            with archive.open(candidates[0]) as input_file, extracted.open("wb") as output_file:
                shutil.copyfileobj(input_file, output_file)
            return extracted
    except zipfile.BadZipFile as error:
        raise ValueError(f"not a valid ZIP archive: {source}") from error


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Prepare a Gizmoduck Switch port from an official ZIP or Gizmoduck.exe"
    )
    parser.add_argument(
        "source", type=Path,
        help="official Gizmoduck Windows ZIP (preferred) or an already extracted Gizmoduck.exe",
    )
    parser.add_argument("--work-dir", type=Path, default=ROOT / ".work" / "gizmoduck-port")
    parser.add_argument("--output", type=Path, default=ROOT / "release" / "switch" / "gizmoduck")
    parser.add_argument("--replace", action="store_true", help="replace an existing work/output directory")
    parser.add_argument("--aar", type=Path, help="already downloaded official Godot Android AAR")
    parser.add_argument("--runtime-sha256", help="optional expected SHA-256 of the AAR")
    parser.add_argument("--cjk-font", type=Path, help="use a local Noto Sans CJK Korean Regular OTF")
    parser.add_argument("--font-url", default=DEFAULT_FONT_URL, help="official URL used when --cjk-font is absent")
    parser.add_argument("--skip-build", action="store_true", help="use an already built gizmoduck.nro")
    args = parser.parse_args()

    source = args.source.resolve()
    if not source.is_file():
        raise SystemExit(f"source file was not found: {source}")
    work = args.work_dir.resolve()
    output = args.output.resolve()
    if (work.exists() or output.exists()) and not args.replace:
        raise SystemExit("work/output directory already exists; pass --replace to replace generated files")
    if args.replace:
        for directory in (work, output):
            if directory.exists():
                shutil.rmtree(directory)

    try:
        exe = source_executable(source, work)
    except ValueError as error:
        raise SystemExit(error) from error

    assets = work / "assets"
    pck = work / "game.pck"
    runtime = work / "runtime"
    font = args.cjk_font.resolve() if args.cjk_font else work / FONT_NAME

    run([sys.executable, "scripts/prepare_game.py", str(exe), "--output", str(assets), "--clean"])
    run([sys.executable, "scripts/make_pck.py", str(exe), "--output", str(pck)])
    runtime_command = [sys.executable, "scripts/prepare_runtime.py", "--output", str(runtime)]
    if args.aar:
        runtime_command += ["--aar", str(args.aar.resolve())]
    if args.runtime_sha256:
        runtime_command += ["--sha256", args.runtime_sha256]
    run(runtime_command)
    if not args.cjk_font:
        download_font(font, args.font_url)
    if not font.is_file():
        raise SystemExit(f"CJK font was not found: {font}")

    run([
        powershell(), "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
        "scripts/extract_original_icon.ps1", "-Executable", str(exe),
        "-Output", "assets/icon.jpg",
    ])
    if not args.skip_build:
        run(["make"])
    nro = ROOT / "gizmoduck.nro"
    if not nro.is_file():
        raise SystemExit(f"NRO was not found: {nro}; run make or omit --skip-build")
    run([
        sys.executable, "scripts/package_sd.py", "--nro", str(nro),
        "--runtime", str(runtime), "--assets", str(assets), "--pck", str(pck),
        "--cjk-font", str(font), "--output", str(output), "--replace",
    ])
    run([sys.executable, "scripts/verify_sd_layout.py", str(output)])
    print("\nReady to copy:", output)


if __name__ == "__main__":
    main()
