"""The brand's interface fonts, registered at startup, by file.   RNV-FONT-SYNC, 2026-11-02

Ruled by Chris on 1 November (BRAND_TYPE.md rev 18, and ruling 107 A): interface
text that is not set in the mark, Montserrat Black, is set in TYPE["body"],
Inter, and code and fixed-width text in TYPE["mono"], JetBrains Mono. They
replace Arial, Segoe UI, Consolas and Courier.

tools/sync_fonts.py writes the files from rnv-brand at the pinned commit into
resources/fonts/, one TrueType file per weight, and writes fonts.json, which
says which file serves which role. This module reads fonts.json, registers
each file with Qt, and asks Qt for the family the files registered under. It
never asks for a typed name: a font file's name table can differ from its
family's name (the brand's Montserrat woff2 registers as "Montserrat Thin"),
and a typed name that misses falls to another face without a word.

A file can register under more than one name: on Windows, Inter's 500 file
registers as "Inter" and as "Inter Medium". A role's family is the name every
one of its files registered under, so each weight is found under it.

Before register() has run, or where a file did not load, family() gives the
family fonts.json names, and Qt falls back from it as it would for any face
it lacks. Latin and Latin Extended only, as the brand's files are: a
character outside them is drawn in the system's face.

THE SAME FILE IN EVERY APPLICATION. Only the folder it is given differs.
"""
from __future__ import annotations

import json
from pathlib import Path

_registered: dict[str, str] = {}
_manifest: dict | None = None
_folder: Path | None = None

#: Where fonts.json is, beside this file's application, unless register() is told.
_DEFAULT_FOLDER = Path(__file__).resolve().parent.parent / "resources" / "fonts"


def manifest(folder: str | Path | None = None) -> dict:
    """fonts.json, as tools/sync_fonts.py wrote it. Empty if it is not there."""
    global _manifest
    path = Path(folder or _folder or _DEFAULT_FOLDER) / "fonts.json"
    if _manifest is None or folder is not None:
        try:
            _manifest = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            _manifest = {}
    return _manifest


def register(folder: str | Path | None = None) -> dict[str, str]:
    """Register every file fonts.json names, once. A QGuiApplication must exist.

    Returns {role: the family Qt reported for that role's files}, for each
    role whose files loaded. Calling it again returns the same, and loads
    nothing twice.

    The family is a name Qt reported for every file of the role that loaded;
    of those, the one fonts.json names if it is among them, and otherwise
    the first in order. A role none of whose files loaded is left out.
    """
    global _folder
    if _registered:
        return dict(_registered)
    from PyQt6.QtGui import QFontDatabase

    _folder = Path(folder) if folder is not None else _DEFAULT_FOLDER
    for role, entry in manifest(_folder).get("roles", {}).items():
        common: list[str] | None = None
        for item in entry.get("files", []):
            font_id = QFontDatabase.addApplicationFont(str(_folder / item["file"]))
            if font_id < 0:
                continue
            families = list(QFontDatabase.applicationFontFamilies(font_id))
            common = families if common is None else [f for f in common if f in families]
        if common:
            named = entry.get("family")
            _registered[role] = named if named in common else common[0]
    return dict(_registered)


def family(role: str) -> str:
    """The family to ask Qt for, for 'body' or 'mono'."""
    if role in _registered:
        return _registered[role]
    named = manifest().get("roles", {}).get(role, {}).get("family")
    if named:
        return named
    return "monospace" if role == "mono" else "sans-serif"


def css(role: str) -> str:
    """The family as a stylesheet names it, with the generic family after it."""
    generic = "monospace" if role == "mono" else "sans-serif"
    return f'"{family(role)}", {generic}'


def font(role: str, size: int = 10, weight: int | None = None):
    """A QFont in the role's family, at a point size, and a weight if given (400, 600...)."""
    from PyQt6.QtGui import QFont

    result = QFont(family(role), size)
    if role == "mono":
        result.setStyleHint(QFont.StyleHint.Monospace)
    if weight is not None:
        result.setWeight(QFont.Weight(weight))
    return result


def file_for(role: str, weight: int = 400, style: str = "normal") -> Path | None:
    """The file serving a role at a weight, for a renderer that loads by path (Pillow)."""
    folder = _folder or _DEFAULT_FOLDER
    files = manifest().get("roles", {}).get(role, {}).get("files", [])
    for item in files:
        if item.get("style") == style and str(item.get("weight")) == str(weight):
            path = folder / item["file"]
            return path if path.is_file() else None
    return None
