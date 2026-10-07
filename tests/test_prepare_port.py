import importlib.util
import tempfile
import unittest
import zipfile
from pathlib import Path


MODULE = Path(__file__).parents[1] / "scripts" / "prepare_port.py"
spec = importlib.util.spec_from_file_location("prepare_port", MODULE)
prepare_port = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(prepare_port)


class PreparePortTests(unittest.TestCase):
    def test_keeps_direct_executable_path(self):
        with tempfile.TemporaryDirectory() as temp:
            executable = Path(temp) / "Gizmoduck.exe"
            executable.write_bytes(b"MZ-test")
            self.assertEqual(
                prepare_port.source_executable(executable, Path(temp) / "work"),
                executable,
            )

    def test_extracts_nested_gizmoduck_executable_from_zip(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive_path = root / "Gizmoduck-win64.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("Gizmoduck-1.1.16/Gizmoduck.exe", b"MZ-test")
            executable = prepare_port.source_executable(archive_path, root / "work")
            self.assertEqual(executable.read_bytes(), b"MZ-test")
            self.assertEqual(executable, root / "work" / "source" / "Gizmoduck.exe")

    def test_rejects_archive_without_executable(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive_path = root / "broken.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("readme.txt", "missing executable")
            with self.assertRaisesRegex(ValueError, "exactly one Gizmoduck.exe"):
                prepare_port.source_executable(archive_path, root / "work")


if __name__ == "__main__":
    unittest.main()
