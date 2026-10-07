#!/usr/bin/env python3
"""Create the exact SD-card layout without committing game data or runtimes."""
from __future__ import annotations

import argparse
import shutil
import struct
from pathlib import Path

REQUIRED_RUNTIME = ("libgodot_android.so", "libc++_shared.so")
CJK_FONT_NAME = "NotoSansCJKkr-Regular.otf"

# The Android runtime reports a 16:9 framebuffer, while Gizmoduck's desktop
# build uses an 8:7 design canvas. `expand` preserves the game's intended
# pixel aspect; its unused side area remains black on the Switch LCD.
SWITCH_ASPECT_KEY = b"display/window/stretch/aspect"
SWITCH_ASPECT_VALUE = b"expand"

# `hint_screen_texture` in Gizmoduck's full-screen CRT pass is unreliable in
# the Switch Mesa GLES path: it samples an unfinished backbuffer and produces
# opaque white/black scanlines.  Leave the game's option usable but make its
# Switch implementation a no-op until a separate multi-pass renderer exists.
SWITCH_CRT_SHADER = """shader_type canvas_item;
render_mode unshaded;

void fragment() {
    // The filter node is an overlay. On Switch, sampling its screen texture
    // reads the incomplete GLES backbuffer and turns the entire frame white.
    // Do not draw the overlay until this renderer has a safe copy pass.
    discard;
}
"""


def copy_tree(source: Path, destination: Path) -> None:
    for path in source.rglob("*"):
        relative = path.relative_to(source)
        target = destination / relative
        if path.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        elif path.is_file():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)


def add_project_string_setting(project: Path, key: bytes, value: bytes) -> None:
    """Append a String setting to Godot's simple ECFG project.binary table."""
    data = bytearray(project.read_bytes())
    if data[:4] != b"ECFG":
        raise ValueError(f"{project} is not a Godot ECFG project.binary")
    count = struct.unpack_from("<I", data, 4)[0]
    cursor = 8
    for _ in range(count):
        key_len = struct.unpack_from("<I", data, cursor)[0]
        cursor += 4 + key_len
        value_len = struct.unpack_from("<I", data, cursor)[0]
        cursor += 4 + value_len
    if cursor != len(data):
        raise ValueError(f"unexpected trailing data in {project}")
    # Variant::STRING (4), followed by its byte length and UTF-8 payload.
    # Godot's Variant encoder pads String payloads to a four-byte boundary.
    # Without this padding the loader rejects the final property with
    # ERR_FILE_EOF, silently leaving the original pillarboxed aspect active.
    padding = (-len(value)) % 4
    encoded = struct.pack("<II", 4, len(value)) + value + (b"\0" * padding)
    data += struct.pack("<I", len(key)) + key
    data += struct.pack("<I", len(encoded)) + encoded
    struct.pack_into("<I", data, 4, count + 1)
    project.write_bytes(data)


def apply_switch_overrides(assets: Path) -> None:
    add_project_string_setting(assets / "project.binary", SWITCH_ASPECT_KEY, SWITCH_ASPECT_VALUE)
    shader = assets / "assets" / "shaders" / "crt.gdshader"
    shader.write_text(SWITCH_CRT_SHADER, encoding="utf-8", newline="\n")


def install_cjk_fallback_font(destination: Path, font: Path) -> None:
    """Create the minimal Android system-font tree used by Godot's fallback."""
    fonts = destination / "android_root" / "fonts"
    etc = destination / "android_root" / "etc"
    fonts.mkdir(parents=True, exist_ok=True)
    etc.mkdir(parents=True, exist_ok=True)
    shutil.copy2(font, fonts / CJK_FONT_NAME)
    (etc / "fonts.xml").write_text(
        """<?xml version=\"1.0\" encoding=\"utf-8\"?>
<familyset version=\"21\">
  <family name=\"sans-serif\" lang=\"ko,ja,zh-Hans,zh-Hant\">
    <font weight=\"400\">NotoSansCJKkr-Regular.otf</font>
  </family>
</familyset>
""",
        encoding="utf-8",
        newline="\n",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--nro", type=Path, default=Path("gizmoduck.nro"))
    parser.add_argument("--runtime", type=Path, default=Path("runtime"))
    parser.add_argument("--assets", type=Path, default=Path("game/assets"))
    parser.add_argument("--pck", type=Path, help="optional standalone Godot PCK for faster SD loading")
    parser.add_argument("--cjk-font", type=Path, default=Path(".work/cjk-font") / CJK_FONT_NAME)
    parser.add_argument("--output", type=Path, default=Path("release/switch/gizmoduck"))
    parser.add_argument("--replace", action="store_true", help="replace an existing output directory")
    args = parser.parse_args()

    missing = [path for path in (args.nro, args.assets / "project.binary") if not path.is_file()]
    missing += [args.runtime / name for name in REQUIRED_RUNTIME if not (args.runtime / name).is_file()]
    if not args.cjk_font.is_file():
        missing.append(args.cjk_font)
    if args.pck is not None and not args.pck.is_file():
        missing.append(args.pck)
    if missing:
        raise SystemExit("missing required input:\n" + "\n".join(f"  {path}" for path in missing))
    output = args.output.resolve()
    if output.exists():
        if not args.replace:
            raise SystemExit(f"output already exists: {output} (pass --replace to replace it)")
        shutil.rmtree(output)
    output.mkdir(parents=True)
    shutil.copy2(args.nro, output / "gizmoduck.nro")
    for name in REQUIRED_RUNTIME:
        shutil.copy2(args.runtime / name, output / name)
    copy_tree(args.assets, output / "assets")
    apply_switch_overrides(output / "assets")
    install_cjk_fallback_font(output, args.cjk_font)
    if args.pck is not None:
        shutil.copy2(args.pck, output / "game.pck")
    (output / "save").mkdir()
    print(output)


if __name__ == "__main__":
    main()
