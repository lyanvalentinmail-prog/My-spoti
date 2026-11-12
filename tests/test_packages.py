from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("build_extensions", ROOT / "scripts" / "build_extensions.py")
builder = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(builder)


class ExtensionPackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.extensions = builder.discover_extensions()
        cls.manifests = {
            slug: json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
            for slug, directory in cls.extensions.items()
        }

    def test_extensions_are_separate_and_valid(self) -> None:
        self.assertEqual({"marea-nocturna", "musica-abierta"}, set(self.extensions))
        ids = []
        for slug, directory in self.extensions.items():
            manifest = builder.validate_extension(directory)
            ids.append(manifest["id"])
            self.assertEqual("1.0.0", manifest["version"], slug)
        self.assertEqual(len(ids), len(set(ids)))

    def test_each_package_is_deterministic_and_importable(self) -> None:
        for slug, directory in self.extensions.items():
            with self.subTest(extension=slug), tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
                package_a = builder.build_extension(directory, Path(first))
                package_b = builder.build_extension(directory, Path(second))
                self.assertEqual(hashlib.sha256(package_a.read_bytes()).digest(), hashlib.sha256(package_b.read_bytes()).digest())
                self.assertLessEqual(package_a.stat().st_size, builder.MAX_ZIP)
                with zipfile.ZipFile(package_a) as archive:
                    self.assertEqual(list(builder.PACKAGE_FILES), archive.namelist())
                    self.assertTrue(all("/" not in name for name in archive.namelist()))
                    manifest = json.loads(archive.read("manifest.json"))
                    self.assertEqual(self.manifests[slug]["id"], manifest["id"])
                    width, height = builder.png_dimensions(archive.read("icon.png"))
                    self.assertEqual((256, 256), (width, height))

    def test_checked_in_packages_match_fresh_builds(self) -> None:
        for slug, directory in self.extensions.items():
            manifest = self.manifests[slug]
            expected = builder.package_path(manifest)
            with self.subTest(extension=slug):
                self.assertTrue(expected.is_file(), f"Build the package first: {expected}")
                with tempfile.TemporaryDirectory() as output:
                    fresh = builder.build_extension(directory, Path(output))
                    self.assertEqual(expected.read_bytes(), fresh.read_bytes())

    def test_theme_has_no_data_or_network_access(self) -> None:
        manifest = self.manifests["marea-nocturna"]
        self.assertEqual(["ui.style"], [action["name"] for action in manifest["actions"]])
        self.assertNotIn("media", manifest)
        self.assertIn("ui", manifest)

    def test_download_extension_has_a_narrow_source_contract(self) -> None:
        manifest = self.manifests["musica-abierta"]
        actions = {action["name"]: action for action in manifest["actions"]}
        self.assertEqual({"download.source", "network"}, set(actions))
        self.assertEqual(["archive.org"], actions["network"]["hosts"])
        self.assertEqual(["archive.org", "*.archive.org"], manifest["media"]["hosts"])
        self.assertNotIn("spotify.raw", actions)
        self.assertNotIn("audio.source", actions)
        self.assertEqual("tools", manifest["category"])

    def test_readme_points_to_independent_releases(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("releases/tag/marea-nocturna-v1.0.0", readme)
        self.assertIn("releases/tag/musica-abierta-v1.0.0", readme)
        self.assertIn("mareanocturna-1.0.0.zip", readme)
        self.assertIn("musicaabierta-1.0.0.zip", readme)


if __name__ == "__main__":
    unittest.main()
