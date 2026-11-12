#!/usr/bin/env python3
"""Validate and deterministically package the Orpheon extensions in this repo."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
EXTENSIONS_DIR = ROOT / "extensions"
PACKAGE_DIR = ROOT / "packages"
PACKAGE_FILES = ("manifest.json", "main.js", "icon.png", "LICENSE", "README.md")
ID_RE = re.compile(r"^[a-z][a-z0-9_]*(\.[a-z0-9_]+)+$")
HOST_RE = re.compile(r"^(\*|(\*\.)?[a-z0-9](?:[a-z0-9-]*[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]*[a-z0-9])?)+)$")
TAG_RE = re.compile(r"^[a-z0-9][a-z0-9 -]{0,23}$")
LANG_RE = re.compile(r"^[A-Za-z]{2,3}(?:[-_][A-Za-z0-9]{2,8}){0,2}$")
HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}(?:[0-9A-Fa-f]{2})?$")
VERSION_RE = re.compile(r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?$")
KNOWN_ACTIONS = {"ui.style", "download.source", "network"}
KNOWN_COLORS = {"accent", "background", "surface"}
KNOWN_PARTS = {"home.dj", "player.lyrics-card", "player.source", "player.capsule"}
EXPECTED_TABS = {"home", "search", "library"}
MAX_ZIP = 2 * 1024 * 1024
MAX_SCRIPT = 1024 * 1024
MAX_ICON = 256 * 1024
FIXED_DATE = (1980, 1, 1, 0, 0, 0)


class ValidationError(ValueError):
    pass


def fail(message: str) -> None:
    raise ValidationError(message)


def discover_extensions() -> dict[str, Path]:
    return {
        path.name: path
        for path in sorted(EXTENSIONS_DIR.iterdir())
        if path.is_dir() and (path / "manifest.json").is_file()
    }


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


def validate_text(value: Any, field: str, minimum: int, maximum: int) -> None:
    if not isinstance(value, str) or len(value) < minimum or len(value) > maximum or (minimum and not value.strip()):
        fail(f"{field} must contain {minimum} to {maximum} characters")


def validate_welcome(welcome: Any, field: str = "welcome") -> None:
    if welcome is None:
        return
    if not isinstance(welcome, dict):
        fail(f"{field} must be an object")
    message = welcome.get("message", "")
    steps = welcome.get("steps", [])
    if not isinstance(message, str) or len(message) > 600:
        fail(f"{field}.message must be at most 600 characters")
    if not isinstance(steps, list) or len(steps) > 5:
        fail(f"{field}.steps must contain at most 5 steps")
    if any(not isinstance(step, str) or not step.strip() or len(step) > 160 for step in steps):
        fail(f"{field}.steps entries must contain 1 to 160 characters")
    if not message.strip() and not steps:
        fail(f"{field} must contain a message or steps")


def validate_hosts(hosts: Any, field: str, allow_any: bool) -> None:
    if not isinstance(hosts, list) or not hosts:
        fail(f"{field} must list at least one host")
    for host in hosts:
        if not isinstance(host, str) or not HOST_RE.fullmatch(host) or (host == "*" and not allow_any):
            fail(f"{field} contains an invalid host: {host!r}")


def validate_ui(ui: Any) -> None:
    if not isinstance(ui, dict) or not any(ui.get(key) for key in ("colors", "hide", "order", "styles", "blocks")):
        fail("ui.style requires a non-empty ui object")
    colors = ui.get("colors", {})
    if not isinstance(colors, dict) or set(colors) - KNOWN_COLORS:
        fail("ui.colors includes an unsupported colour")
    for key, color in colors.items():
        if not isinstance(color, str) or not HEX_RE.fullmatch(color):
            fail(f"ui.colors.{key} is not #RRGGBB or #AARRGGBB")
        if key != "accent" and luminance(color) > 0.2:
            fail(f"ui.colors.{key} is too light for Orpheon's white text")
    hidden = ui.get("hide", [])
    if not isinstance(hidden, list) or len(hidden) > 20 or any(part not in KNOWN_PARTS for part in hidden):
        fail("ui.hide includes an unsupported part")
    tabs = ui.get("order", {}).get("nav")
    if tabs is not None and (not isinstance(tabs, list) or len(tabs) != 3 or set(tabs) != EXPECTED_TABS):
        fail("ui.order.nav must contain home, search and library exactly once")
    scale = ui.get("styles", {}).get("text", {}).get("scale")
    if scale is not None and (not isinstance(scale, (int, float)) or not 0.85 <= scale <= 1.3):
        fail("ui.styles.text.scale must be between 0.85 and 1.3")


def validate_manifest(manifest: dict[str, Any]) -> None:
    extension_id = manifest.get("id", "")
    if not isinstance(extension_id, str) or not ID_RE.fullmatch(extension_id):
        fail("manifest id must be a lower-case reverse-domain id")
    for key, maximum in (("name", 40), ("version", 20), ("author", 60)):
        validate_text(manifest.get(key), key, 1, maximum)
    if not VERSION_RE.fullmatch(manifest["version"]):
        fail("version must look like 1.2.3 or 1.2.3-beta.1")
    if not isinstance(manifest.get("versionCode", 1), int) or manifest.get("versionCode", 1) < 1:
        fail("versionCode must be a positive integer")
    if manifest.get("apiVersion", 1) != 1:
        fail("this repository targets Orpheon extension API 1")
    if not isinstance(manifest.get("description", ""), str) or len(manifest.get("description", "")) > 500:
        fail("description must be at most 500 characters")
    if manifest.get("minAppVersion") is not None and not VERSION_RE.fullmatch(str(manifest["minAppVersion"])):
        fail("minAppVersion is invalid")
    if not isinstance(manifest.get("changelog", ""), str) or len(manifest.get("changelog", "")) > 2000:
        fail("changelog must be at most 2000 characters")
    validate_welcome(manifest.get("welcome"))

    actions = manifest.get("actions")
    if not isinstance(actions, list) or not actions:
        fail("at least one action is required")
    action_names: list[str] = []
    for action in actions:
        if not isinstance(action, dict):
            fail("every action must be an object")
        name = action.get("name")
        if name not in KNOWN_ACTIONS:
            fail(f"unknown action in this repository: {name!r}")
        validate_text(action.get("why"), f"action {name} reason", 1, 80)
        hosts = action.get("hosts", [])
        if name == "network":
            validate_hosts(hosts, "network.hosts", allow_any=True)
        elif hosts:
            fail(f"only network may declare hosts, not {name}")
        action_names.append(name)
    if len(action_names) != len(set(action_names)):
        fail("an action is listed more than once")

    if "ui.style" in action_names:
        validate_ui(manifest.get("ui"))
    elif "ui" in manifest:
        fail("ui requires the ui.style action")
    if "download.source" in action_names and manifest.get("category") != "tools":
        fail("download sources must use the tools category")
    if manifest.get("media") is not None:
        media = manifest["media"]
        if not isinstance(media, dict):
            fail("media must be an object")
        validate_hosts(media.get("hosts"), "media.hosts", allow_any=False)

    tags = manifest.get("tags", [])
    if not isinstance(tags, list) or len(tags) > 8 or any(not isinstance(tag, str) or not TAG_RE.fullmatch(tag) for tag in tags):
        fail("tags do not follow Orpheon's manifest rules")

    translations = manifest.get("translations", {})
    if not isinstance(translations, dict) or len(translations) > 80:
        fail("translations must be an object with at most 80 languages")
    action_set = set(action_names)
    for language, translation in translations.items():
        if not LANG_RE.fullmatch(language) or not isinstance(translation, dict):
            fail(f"invalid translation: {language!r}")
        if "name" in translation:
            validate_text(translation["name"], f"translations.{language}.name", 1, 40)
        if len(translation.get("description", "")) > 500 or len(translation.get("changelog", "")) > 2000:
            fail(f"translations.{language} contains text that is too long")
        validate_welcome(translation.get("welcome"), f"translations.{language}.welcome")
        for name, reason in translation.get("actions", {}).items():
            if name not in action_set:
                fail(f"translations.{language}.actions includes undeclared action {name}")
            validate_text(reason, f"translations.{language}.actions.{name}", 1, 80)


def validate_extension(directory: Path) -> dict[str, Any]:
    missing = [name for name in PACKAGE_FILES if not (directory / name).is_file()]
    if missing:
        fail(f"{directory.name}: missing package files: {', '.join(missing)}")
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        fail(f"{directory.name}: manifest root must be an object")
    validate_manifest(manifest)

    main = manifest.get("main", "main.js")
    icon = manifest.get("icon", "icon.png")
    if main != "main.js" or icon != "icon.png":
        fail(f"{directory.name}: this repository packages main.js and icon.png")
    if (directory / main).stat().st_size > MAX_SCRIPT:
        fail(f"{directory.name}: main script is larger than 1 MB")
    icon_data = (directory / icon).read_bytes()
    if len(icon_data) > MAX_ICON:
        fail(f"{directory.name}: icon is larger than 256 KB")
    width, height = png_dimensions(icon_data)
    if width != height or width > 256:
        fail(f"{directory.name}: icon must be square and no larger than 256 × 256")
    return manifest


def package_path(manifest: dict[str, Any], output_dir: Path = PACKAGE_DIR) -> Path:
    return output_dir / f"{manifest['id']}-{manifest['version']}.zip"


def build_extension(directory: Path, output_dir: Path = PACKAGE_DIR) -> Path:
    manifest = validate_extension(directory)
    output_dir.mkdir(parents=True, exist_ok=True)
    output = package_path(manifest, output_dir)
    with tempfile.NamedTemporaryFile(dir=output_dir, suffix=".zip", delete=False) as temporary:
        temp_path = Path(temporary.name)
    try:
        with zipfile.ZipFile(temp_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for name in PACKAGE_FILES:
                info = zipfile.ZipInfo(name, FIXED_DATE)
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                archive.writestr(info, (directory / name).read_bytes(), compresslevel=9)
        if temp_path.stat().st_size > MAX_ZIP:
            fail(f"{directory.name}: package is larger than 2 MB")
        temp_path.replace(output)
    finally:
        temp_path.unlink(missing_ok=True)
    return output


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def selected_directories(slugs: list[str]) -> list[Path]:
    extensions = discover_extensions()
    if not slugs:
        return list(extensions.values())
    unknown = set(slugs) - set(extensions)
    if unknown:
        fail(f"unknown extension(s): {', '.join(sorted(unknown))}")
    return [extensions[slug] for slug in slugs]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--extension", action="append", default=[], help="extension directory name; repeatable")
    parser.add_argument("--check", action="store_true", help="validate without writing packages")
    parser.add_argument("--output-dir", type=Path, default=PACKAGE_DIR)
    args = parser.parse_args()
    try:
        directories = selected_directories(args.extension)
        for directory in directories:
            if args.check:
                manifest = validate_extension(directory)
                print(f"✓ {directory.name}: {manifest['name']} {manifest['version']} is valid")
            else:
                output = build_extension(directory, args.output_dir)
                shown = output.relative_to(ROOT) if output.is_relative_to(ROOT) else output
                print(f"✓ {directory.name}: {shown}")
                print(f"  sha256 {sha256(output)}")
        return 0
    except (OSError, ValidationError, json.JSONDecodeError) as error:
        print(f"✗ {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
