from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("build_extension", ROOT / "scripts" / "build_extension.py")
builder = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(builder)


class ExtensionPackageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))

    def test_sources_follow_orpheon_manifest_rules(self) -> None:
        builder.validate_sources()

    def test_theme_is_dark_and_changes_only_supported_ui(self) -> None:
        ui = self.manifest["ui"]
        self.assertEqual({"accent", "background", "surface"}, set(ui["colors"]))
        self.assertLessEqual(builder.luminance(ui["colors"]["background"]), 0.2)
        self.assertLessEqual(builder.luminance(ui["colors"]["surface"]), 0.2)
        self.assertEqual({"home", "search", "library"}, set(ui["order"]["nav"]))
        self.assertTrue(set(ui["hide"]).issubset(builder.KNOWN_PARTS))
        self.assertEqual(["ui.style"], [action["name"] for action in self.manifest["actions"]])

    def test_package_is_deterministic_and_importable(self) -> None:
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            package_a = builder.build(Path(first))
            package_b = builder.build(Path(second))
            bytes_a = package_a.read_bytes()
            bytes_b = package_b.read_bytes()
            self.assertEqual(hashlib.sha256(bytes_a).digest(), hashlib.sha256(bytes_b).digest())
            self.assertLessEqual(len(bytes_a), builder.MAX_ZIP)

            with zipfile.ZipFile(package_a) as archive:
                self.assertEqual(list(builder.ALLOWED_FILES), archive.namelist())
                self.assertTrue(all("/" not in name for name in archive.namelist()))
                packaged_manifest = json.loads(archive.read("manifest.json"))
                self.assertEqual(self.manifest["id"], packaged_manifest["id"])
                self.assertEqual(self.manifest["version"], packaged_manifest["version"])
                width, height = builder.png_dimensions(archive.read("icon.png"))
                self.assertEqual((256, 256), (width, height))

    def test_checked_in_package_matches_a_fresh_build(self) -> None:
        expected = builder.package_path(self.manifest)
        self.assertTrue(expected.is_file(), f"Build the package first: {expected}")
        with tempfile.TemporaryDirectory() as output:
            fresh = builder.build(Path(output))
            self.assertEqual(expected.read_bytes(), fresh.read_bytes())


if __name__ == "__main__":
    unittest.main()
