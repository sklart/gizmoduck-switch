import importlib.util
import tempfile
import unittest
from pathlib import Path


MODULE = Path(__file__).parents[1] / "scripts" / "package_sd.py"
spec = importlib.util.spec_from_file_location("package_sd", MODULE)
package_sd = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(package_sd)


class PackageSdTests(unittest.TestCase):
    def test_copy_tree_preserves_nested_asset_paths(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "assets-source"
            (source / "nested").mkdir(parents=True)
            (source / "project.binary").write_bytes(b"project")
            (source / "nested" / "scene.scn").write_bytes(b"scene")
            destination = root / "assets-destination"
            package_sd.copy_tree(source, destination)
            self.assertEqual((destination / "project.binary").read_bytes(), b"project")
            self.assertEqual((destination / "nested" / "scene.scn").read_bytes(), b"scene")

    def test_required_runtime_names_are_fixed(self):
        self.assertEqual(package_sd.REQUIRED_RUNTIME,
                         ("libgodot_android.so", "libc++_shared.so"))

    def test_switch_overrides_expand_canvas_and_neutralize_crt(self):
        with tempfile.TemporaryDirectory() as temp:
            assets = Path(temp) / "assets"
            (assets / "assets" / "shaders").mkdir(parents=True)
            project = assets / "project.binary"
            project.write_bytes(b"ECFG" + (0).to_bytes(4, "little"))
            (assets / "assets" / "shaders" / "crt.gdshader").write_text("original")

            package_sd.apply_switch_overrides(assets)

            data = project.read_bytes()
            self.assertEqual(int.from_bytes(data[4:8], "little"), 1)
            self.assertIn(package_sd.SWITCH_ASPECT_KEY, data)
            self.assertIn(package_sd.SWITCH_ASPECT_VALUE, data)
            self.assertIn("discard;",
                          (assets / "assets" / "shaders" / "crt.gdshader").read_text())

    def test_installs_cjk_font_as_android_fallback(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "font.otf"
            source.write_bytes(b"test font")
            package_sd.install_cjk_fallback_font(root / "output", source)
            installed = root / "output" / "android_root" / "fonts" / package_sd.CJK_FONT_NAME
            self.assertEqual(installed.read_bytes(), b"test font")
            config = (root / "output" / "android_root" / "etc" / "fonts.xml").read_text()
            self.assertIn(package_sd.CJK_FONT_NAME, config)
            self.assertIn('lang="ko,ja,zh-Hans,zh-Hant"', config)


if __name__ == "__main__":
    unittest.main()
