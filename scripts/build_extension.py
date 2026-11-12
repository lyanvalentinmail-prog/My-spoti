#!/usr/bin/env python3
"""Validate and build the deterministic Orpheon extension package."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE_DIR = ROOT / "packages"
ALLOWED_FILES = ("manifest.json", "main.js", "icon.png", "LICENSE", "README.md")
ID_RE = re.compile(r"^[a-z][a-z0-9_]*(\.[a-z0-9_]+)+$")
HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}(?:[0-9A-Fa-f]{2})?$")
TAG_RE = re.compile(r"^[a-z0-9][a-z0-9 -]{0,23}$")
KNOWN_COLORS = {"accent", "background", "surface"}
KNOWN_PARTS = {"home.dj", "player.lyrics-card", "player.source", "player.capsule"}
EXPECTED_TABS = {"home", "search", "library"}
MAX_ZIP = 2 * 1024 * 1024
MAX_SCRIPT = 1024 * 1024
MAX_ICON = 256 * 1024
FIXED_DATE = (1980, 1, 1, 0, 0, 0)


def fail(message: str) -> None:
    raise ValueError(message)


def png_dimensions(data: bytes) -> tuple[int, int]:
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        fail("icon.png is not a valid PNG")
    return struct.unpack(">II", data[16:24])


def channel_luminance(value: int) -> float:
    channel = value / 255.0
    return channel / 12.92 if channel <= 0.03928 else ((channel + 0.055) / 1.055) ** 2.4


def luminance(color: str) -> float:
    value = color.removeprefix("#")
    if len(value) == 8:
        if value[:2].lower() != "ff":
            fail(f"background colour {color} must be opaque")
        value = value[2:]
    red, green, blue = (int(value[index : index + 2], 16) for index in (0, 2, 4))
    return 0.2126 * channel_luminance(red) + 0.7152 * channel_luminance(green) + 0.0722 * channel_luminance(blue)


def validate_manifest(manifest: dict) -> None:
    extension_id = manifest.get("id", "")
    if not ID_RE.fullmatch(extension_id):
        fail("manifest id must be a lower-case reverse-domain id")
    for key, maximum in (("name", 40), ("version", 20), ("author", 60)):
        value = manifest.get(key)
        if not isinstance(value, str) or not value.strip() or len(value) > maximum:
            fail(f"manifest {key} must contain 1 to {maximum} characters")
    if manifest.get("versionCode", 1) < 1:
        fail("versionCode must be positive")
    if manifest.get("apiVersion", 1) != 1:
        fail("this package targets Orpheon extension API 1")
    if len(manifest.get("description", "")) > 500:
        fail("description is longer than 500 characters")

    actions = manifest.get("actions")
    if not isinstance(actions, list) or not actions:
        fail("at least one action is required")
    names: list[str] = []
    for action in actions:
        name = action.get("name")
        why = action.get("why")
        if name != "ui.style":
            fail(f"unexpected action for a look-only extension: {name!r}")
        if not isinstance(why, str) or not why.strip() or len(why) > 80:
            fail("every action reason must contain 1 to 80 characters")
        names.append(name)
    if len(names) != len(set(names)):
        fail("an action is listed more than once")

    tags = manifest.get("tags", [])
    if len(tags) > 8 or any(not isinstance(tag, str) or not TAG_RE.fullmatch(tag) for tag in tags):
        fail("tags do not follow Orpheon's manifest rules")

    ui = manifest.get("ui")
    if not isinstance(ui, dict) or not any(ui.get(key) for key in ("colors", "hide", "order", "styles", "blocks")):
        fail("ui.style requires a non-empty ui object")
    colors = ui.get("colors", {})
    unknown_colors = set(colors) - KNOWN_COLORS
    if unknown_colors:
        fail(f"unknown UI colours: {', '.join(sorted(unknown_colors))}")
    for key, color in colors.items():
        if not isinstance(color, str) or not HEX_RE.fullmatch(color):
            fail(f"ui.colors.{key} is not #RRGGBB or #AARRGGBB")
        if key != "accent" and luminance(color) > 0.2:
            fail(f"ui.colors.{key} is too light for Orpheon's white text")

    hidden = ui.get("hide", [])
    if len(hidden) > 20 or any(part not in KNOWN_PARTS for part in hidden):
        fail("ui.hide includes an unsupported part")
    tabs = ui.get("order", {}).get("nav")
    if tabs is not None and (len(tabs) != 3 or set(tabs) != EXPECTED_TABS):
        fail("ui.order.nav must contain home, search and library exactly once")
    scale = ui.get("styles", {}).get("text", {}).get("scale")
    if scale is not None and (not isinstance(scale, (int, float)) or not 0.85 <= scale <= 1.3):
        fail("ui.styles.text.scale must be between 0.85 and 1.3")

    translations = manifest.get("translations", {})
    action_names = set(names)
    for language, translation in translations.items():
        if not re.fullmatch(r"[A-Za-z]{2,3}(?:[-_][A-Za-z0-9]{2,8}){0,2}", language):
            fail(f"invalid translation language tag: {language}")
        for name, reason in translation.get("actions", {}).items():
            if name not in action_names or not reason.strip() or len(reason) > 80:
                fail(f"invalid translated reason for {name}")


def validate_sources() -> dict:
    missing = [name for name in ALLOWED_FILES if not (ROOT / name).is_file()]
    if missing:
        fail(f"missing package files: {', '.join(missing)}")
    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    validate_manifest(manifest)

    script_size = (ROOT / manifest.get("main", "main.js")).stat().st_size
    if script_size > MAX_SCRIPT:
        fail("main script is larger than 1 MB")
    icon_data = (ROOT / manifest.get("icon", "icon.png")).read_bytes()
    if len(icon_data) > MAX_ICON:
        fail("icon is larger than 256 KB")
    width, height = png_dimensions(icon_data)
    if width != height or width > 256:
        fail("icon must be square and no larger than 256 × 256")
    return manifest


def package_path(manifest: dict, output_dir: Path = PACKAGE_DIR) -> Path:
    return output_dir / f"{manifest['id']}-{manifest['version']}.zip"


def build(output_dir: Path = PACKAGE_DIR) -> Path:
    manifest = validate_sources()
    output_dir.mkdir(parents=True, exist_ok=True)
    output = package_path(manifest, output_dir)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name in ALLOWED_FILES:
            info = zipfile.ZipInfo(name, FIXED_DATE)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, (ROOT / name).read_bytes(), compresslevel=9)
    if output.stat().st_size > MAX_ZIP:
        output.unlink(missing_ok=True)
        fail("package is larger than 2 MB")
    return output


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="validate source files without writing a package")
    parser.add_argument("--output-dir", type=Path, default=PACKAGE_DIR)
    args = parser.parse_args()
    try:
        if args.check:
            manifest = validate_sources()
            print(f"✓ {manifest['name']} {manifest['version']} is valid")
        else:
            output = build(args.output_dir)
            print(f"✓ {output.relative_to(ROOT) if output.is_relative_to(ROOT) else output}")
            print(f"sha256 {sha256(output)}")
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"✗ {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
