import importlib.util
import struct
import tempfile
import unittest
from pathlib import Path


MODULE = Path(__file__).parents[1] / "scripts" / "verify_sd_layout.py"
spec = importlib.util.spec_from_file_location("verify_sd_layout", MODULE)
verify_sd_layout = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(verify_sd_layout)


class VerifySdLayoutTests(unittest.TestCase):
    def test_aarch64_elf_detection(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "runtime.so"
            header = bytearray(20)
            header[:4] = b"\x7fELF"
            header[4] = 2
            struct.pack_into("<H", header, 18, 183)
            path.write_bytes(header)
            self.assertTrue(verify_sd_layout.elf_is_aarch64(path))

    def test_rejects_non_aarch64_elf(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "runtime.so"
            path.write_bytes(b"not an elf")
            self.assertFalse(verify_sd_layout.elf_is_aarch64(path))

    def test_detects_embedded_nro_control_assets(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "test.nro"
            asset_offset = 0x80
            data = bytearray(asset_offset + 0x30 + 32)
            data[asset_offset:asset_offset + 4] = b"ASET"
            struct.pack_into("<QQQQ", data, asset_offset + 8,
                             0x30, 16, 0x40, 16)
            data[asset_offset + 0x30:asset_offset + 0x33] = b"\xff\xd8\xff"
            path.write_bytes(data)
            self.assertTrue(verify_sd_layout.nro_has_control_assets(path))


if __name__ == "__main__":
    unittest.main()
