"""The interface fonts are the brand's, at the pin, and Qt loads them.   RNV-FONT-SYNC

Ruled by Chris on 1 November (BRAND_TYPE.md rev 18, and ruling 107 A): interface
text that is not in the mark is set in TYPE["body"], Inter, and code and
fixed-width text in TYPE["mono"], JetBrains Mono. tools/sync_fonts.py makes
their files, one TrueType file per weight, from rnv-brand's woff2 files at the
commit pinned in tests/requirements-dev.txt, copies their licenses beside
them in resources/fonts/, and writes fonts.json. utils/brand_fonts.py
registers those files at startup, by file. The same three files, the tool,
the module and this test, are in all five applications.

WHAT THIS GUARD HOLDS.

1. resources/fonts/ is what the sync makes at the pin: each face was made
   from the brand files the pin holds, by their sha256, and is the file
   fonts.json records; the licenses and fonts.json are byte for byte. A font
   or license edited, a file left by an older pin, or a pin moved without a
   sync, and this names the file and says what to run. It decodes nothing.
2. Every face is TrueType or OpenType. On Chris's Windows machine, 2
   November, Qt registered none of the brand's woff2 files: Qt on Linux reads
   them through FreeType, and on Windows through DirectWrite or GDI, which
   read TrueType and OpenType only. This guard runs on Linux too, so it holds
   the format, not the platform's luck.
3. Each weight is one file, and that file draws both subsets. Qt keeps one
   file for each family, weight and style, and a second file at the same
   weight replaces the first instead of filling in its characters.
4. Qt loads every file, and registers each role under the family fonts.json
   names. That is what makes the family a stylesheet names by text safe: the
   brand's Montserrat woff2 registers as "Montserrat Thin", and a name that
   misses falls to another face without a word.
5. Each role resolves to its own face at each weight the brand lists, and
   the mono face is fixed-width.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
FONTS = ROOT / "resources" / "fonts"

#: The first bytes of a TrueType or OpenType file: TrueType outlines, CFF outlines, Apple's TrueType.
SFNT = (b"\x00\x01\x00\x00", b"OTTO", b"true")
#: A character from each subset the brand cuts: Basic Latin, Latin-1, and Latin Extended-A.
SUBSET_CHARACTERS = "Aéőž"


def _load(name: str, path: pathlib.Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SYNC = _load("sync_fonts", ROOT / "tools" / "sync_fonts.py")


def _record() -> dict:
    return json.loads((FONTS / "fonts.json").read_text(encoding="utf-8"))


def test_the_fonts_are_what_the_sync_writes_at_the_pin():
    out_of_date, left = SYNC.stale(ROOT)
    assert not out_of_date and not left, (
        "resources/fonts/ is not what the brand holds at the pin: "
        + ", ".join([f"out of date {p}" for p in out_of_date] + [f"no longer listed {p}" for p in left])
        + ". Run: python tools/sync_fonts.py")


def test_the_record_agrees_with_the_files():
    record = _record()
    assert set(record["roles"]) == set(SYNC.ROLES)
    for role, entry in record["roles"].items():
        assert entry["files"], f"{role}: no file"
        assert (FONTS / entry["license"]).is_file(), f"{role}: no {entry['license']}"
        for item in entry["files"]:
            data = (FONTS / item["file"]).read_bytes()
            assert hashlib.sha256(data).hexdigest() == item["sha256"], f"{item['file']} is not the file recorded"
            assert item["from"], f"{item['file']}: the record names no brand file it was made from"
    assert (FONTS / record["mark"]["file"]).is_file() and (FONTS / record["mark"]["license"]).is_file()


def test_every_face_is_a_file_qt_loads_on_windows():
    for entry in _record()["roles"].values():
        for item in entry["files"]:
            head = (FONTS / item["file"]).read_bytes()[:4]
            assert head in SFNT, (
                f"{item['file']} is not TrueType or OpenType (it begins {head!r}); "
                "Qt on Windows would not load it")


def test_each_weight_is_one_file_that_draws_both_subsets(qapp):
    from PyQt6.QtGui import QRawFont

    for role, entry in _record()["roles"].items():
        keys = [(item["weight"], item["style"]) for item in entry["files"]]
        assert len(keys) == len(set(keys)), f"{role}: two files at one weight and style: {sorted(keys)}"
        for item in entry["files"]:
            subsets = {s["subset"] for s in item["from"]}
            assert {"latin", "latin-ext"} <= subsets, f"{item['file']} was made from {sorted(subsets)}"
            raw = QRawFont(str(FONTS / item["file"]), 12)
            assert raw.isValid(), f"Qt could not read {item['file']}"
            missing = [c for c in SUBSET_CHARACTERS if not raw.supportsCharacter(c)]
            assert not missing, f"{item['file']} does not draw {''.join(missing)!r}"


def test_qt_registers_each_role_under_the_family_the_record_names(qapp):
    brand_fonts = _load("brand_fonts_under_test", ROOT / "utils" / "brand_fonts.py")
    registered = brand_fonts.register(FONTS)
    record = _record()
    for role, entry in record["roles"].items():
        assert registered.get(role) == entry["family"], (
            f"{role}: Qt registered {registered.get(role)!r}, and fonts.json names {entry['family']!r}")
        assert brand_fonts.family(role) == entry["family"]


def test_each_role_resolves_to_its_own_face(qapp):
    from PyQt6.QtGui import QFontInfo

    brand_fonts = _load("brand_fonts_resolved", ROOT / "utils" / "brand_fonts.py")
    brand_fonts.register(FONTS)
    for role, entry in _record()["roles"].items():
        for weight in sorted({int(i["weight"]) for i in entry["files"]}):
            info = QFontInfo(brand_fonts.font(role, 12, weight))
            assert info.family() == entry["family"], f"{role} at {weight} resolves to {info.family()!r}"
            assert abs(info.weight() - weight) <= 50, f"{role} asked at {weight} resolves to weight {info.weight()}"
    assert QFontInfo(brand_fonts.font("mono", 12)).fixedPitch(), "the mono face is not fixed-width"
