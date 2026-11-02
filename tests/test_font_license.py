"""Every font this application ships has its license beside it.

Brand Infrastructure, 1 November 2026: each application committed
resources/fonts/Montserrat-Black.ttf with no license file. Montserrat is under
the SIL Open Font License 1.1, which must travel with the font wherever it is
redistributed: a public repository is redistribution, and so is a built
application. The interface faces that came the same day, Inter and JetBrains
Mono, are under it too. Each family's license is in resources/fonts/ as
OFL-<Family>.txt, the text rnv-brand keeps under the same name, written by
tools/sync_fonts.py. The installs and the PyInstaller builds carry the whole
folder, so each license goes where its font goes
(tests/test_install_resources.py holds the installs).

This file is the same in all five applications.
"""
from __future__ import annotations

import json
from pathlib import Path

FONTS = Path(__file__).resolve().parent.parent / "resources" / "fonts"
FONT_SUFFIXES = {".ttf", ".otf", ".woff", ".woff2"}


def _families() -> dict[str, str]:
    """{font file name: its family}: fonts.json for the brand's files, the
    file's own name for the mark's TTF."""
    record = json.loads((FONTS / "fonts.json").read_text(encoding="utf-8"))
    names = {item["file"]: entry["family"]
             for entry in record["roles"].values() for item in entry["files"]}
    names[record["mark"]["file"]] = record["mark"]["family"]
    return names


def test_there_is_a_font_to_check():
    assert any(p.suffix.lower() in FONT_SUFFIXES for p in FONTS.iterdir()), \
        f"no font in {FONTS}: nothing was checked"


def test_every_font_has_its_family_s_open_font_license():
    families = _families()
    for font in sorted(p for p in FONTS.iterdir() if p.suffix.lower() in FONT_SUFFIXES):
        assert font.name in families, f"{font.name} ships and no record says which family it is"
        family = families[font.name]
        license_file = FONTS / ("OFL-" + family.replace(" ", "-") + ".txt")
        assert license_file.is_file(), f"{font.name} ships with no {license_file.name} beside it"
        text = license_file.read_text(encoding="utf-8")
        assert "SIL OPEN FONT LICENSE Version 1.1" in text, f"{license_file.name} is not the OFL 1.1"
        assert f"The {family} Project Authors" in text, f"{license_file.name} is not {family}'s license"
