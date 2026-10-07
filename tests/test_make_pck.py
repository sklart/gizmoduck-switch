import importlib.util
import struct
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
prepare_spec = importlib.util.spec_from_file_location("prepare_game", ROOT / "scripts" / "prepare_game.py")
prepare_game = importlib.util.module_from_spec(prepare_spec)
assert prepare_spec.loader is not None
prepare_spec.loader.exec_module(prepare_game)

import sys
sys.path.insert(0, str(ROOT / "scripts"))
import make_pck


class MakePckTests(unittest.TestCase):
    def test_copies_exact_embedded_pck(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            pack = b"GDPC" + b"payload"
            executable = root / "game.exe"
            executable.write_bytes(b"EXE" + pack + struct.pack("<Q", len(pack)) + b"GDPC")
            output = root / "game.pck"
            self.assertEqual(make_pck.make_pck(executable, output), len(pack))
            self.assertEqual(output.read_bytes(), pack)


if __name__ == "__main__":
    unittest.main()
