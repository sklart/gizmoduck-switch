import hashlib
import importlib.util
import struct
import tempfile
import unittest
from pathlib import Path


MODULE = Path(__file__).parents[1] / "scripts" / "prepare_game.py"
spec = importlib.util.spec_from_file_location("prepare_game", MODULE)
prepare_game = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(prepare_game)


def embedded_pck(path: str, payload: bytes) -> bytes:
    """A minimal Godot 4 executable-embedded PCK for parser tests."""
    file_base = 112
    header = bytearray(file_base)
    header[0:4] = b"GDPC"
    struct.pack_into("<IIIIIQQ", header, 4, 4, 4, 7, 2, 2, file_base, file_base + len(payload))
    record = path.encode("utf-8")
    directory = struct.pack("<I", 1)
    directory += struct.pack("<I", len(record)) + record
    directory += struct.pack("<QQ", 0, len(payload)) + hashlib.md5(payload).digest()
    directory += struct.pack("<I", 0)
    pck = bytes(header) + payload + directory
    return b"MZ" + pck + struct.pack("<Q", len(pck)) + b"GDPC"


class PrepareGameTests(unittest.TestCase):
    def test_extracts_relative_embedded_pck_path(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            executable = root / "game.exe"
            executable.write_bytes(embedded_pck("project.binary", b"project"))
            output = root / "assets"
            report = prepare_game.extract(executable, output)
            self.assertEqual(report["godot"], "4.7.2")
            self.assertEqual(report["file_count"], 1)
            self.assertEqual((output / "project.binary").read_bytes(), b"project")

    def test_rejects_parent_path(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            executable = root / "game.exe"
            executable.write_bytes(embedded_pck("../outside", b"no"))
            with self.assertRaisesRegex(ValueError, "unsafe PCK path"):
                prepare_game.extract(executable, root / "assets")


if __name__ == "__main__":
    unittest.main()
