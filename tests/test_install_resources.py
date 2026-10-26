"""AN INSTALLED COPY CARRIES resources/ (#97 A, 2026-10-24).

THE FAULT IT KEEPS AWAY. `pip install .` built a wheel with no fonts, icons,
button images or background in it. pyproject.toml asked for them as
`"*" = ["resources/**/*"]`, but package data is matched inside each package
directory, and resources/ is not inside core/, ui/ or utils/, so the pattern
matched nothing. The installed app then looked for
site-packages/resources/, found no font and no images, and could not offer
Image mode.

WHAT IT HOLDS, by reading pyproject.toml (no build):
  1. `resources` and each folder in it are packages, so their files install
     beside core/, ui/ and utils/ (setuptools warns that it will drop the
     files of a folder that is not listed);
  2. every file under resources/ matches a package-data pattern of that
     package, matched the way setuptools matches them;
  3. the app looks for resources/ beside utils/, which is where they install.

A wheel built from this repository lists every one of them under resources/.
"""
from __future__ import annotations

import glob
import os
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESOURCES = ROOT / "resources"


def _setuptools() -> dict:
    with open(ROOT / "pyproject.toml", "rb") as f:
        return tomllib.load(f)["tool"]["setuptools"]


def _files_under(folder: Path) -> set[str]:
    return {
        p.relative_to(folder).as_posix()
        for p in folder.rglob("*")
        if p.is_file() and "__pycache__" not in p.parts
    }


def test_resources_and_its_folders_are_installed_as_packages():
    packages = _setuptools()["packages"]
    assert "resources" in packages, (
        f"pyproject.toml packages = {packages}: without 'resources' no "
        f"resource file goes into the wheel")
    folders = {
        ".".join(("resources",) + p.relative_to(RESOURCES).parts)
        for p in RESOURCES.rglob("*")
        if p.is_dir() and "__pycache__" not in p.parts
    }
    assert folders, "resources/ has no folders, so this check proved nothing"
    missing = sorted(folders - set(packages))
    assert not missing, f"add to pyproject.toml packages: {missing}"


def test_every_resource_file_matches_package_data():
    package_data = _setuptools().get("package-data", {})
    patterns = list(package_data.get("resources", [])) + list(package_data.get("*", []))
    matched: set[str] = set()
    for pattern in patterns:
        for hit in glob.glob(pattern, root_dir=RESOURCES, recursive=True):
            if (RESOURCES / hit).is_file():
                matched.add(Path(hit).as_posix())
    on_disk = _files_under(RESOURCES)
    assert on_disk, "resources/ is empty, so this check proved nothing"
    missing = sorted(on_disk - matched)
    assert not missing, f"left out of an installed copy: {missing}"


def test_the_app_looks_for_resources_beside_utils():
    from utils import config
    utils_dir = Path(config.__file__).resolve().parent
    assert "utils" in _setuptools()["packages"]
    assert Path(config.RESOURCES_DIR).resolve() == utils_dir.parent / "resources"
    assert Path(config.FONT_PATH).resolve().is_relative_to(
        Path(config.RESOURCES_DIR).resolve())
    assert os.path.exists(config.FONT_PATH)
