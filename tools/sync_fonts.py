"""Write the brand's interface fonts into this application.   RNV-FONT-SYNC, 2026-11-02

    python tools/sync_fonts.py           write resources/fonts/ from the brand
    python tools/sync_fonts.py --check   write nothing; exit 1 if a file is out of date

Ruled by Chris on 1 November (BRAND_TYPE.md rev 18, and ruling 107 A here): the
applications set their interface text in TYPE["body"], Inter, and their code
and fixed-width text in TYPE["mono"], JetBrains Mono. The mark stays
Montserrat Black, from resources/fonts/Montserrat-Black.ttf, as before.

WHAT IT WRITES, into resources/fonts/:
- one TrueType file for each weight and style the brand's font_files() lists
  for the body and mono families, made from the brand's woff2 files at the
  pinned commit: each woff2 decoded, and the Latin and Latin Extended
  subsets of one weight joined into one file. Each character is drawn by the
  subset the brand's own font_faces() gives it, by its unicode-range, as a
  browser draws the brand's site: where two ranges hold a character, the one
  declared last, which is Latin;
- each of those families' license, OFL-<Family>.txt, and the mark's,
  OFL-Montserrat.txt, which the bundled TTF owes, byte for byte;
- fonts.json, the record the application reads at startup: the pin, and for
  each role its family and its files, with each file's weight, style and
  sha256, and the sha256 and unicode-range of each brand file it was made
  from.

WHY NOT THE WOFF2 FILES THEMSELVES. Measured on Chris's Windows machine, 2
November: Qt registered none of them. On Linux Qt hands an application font to
FreeType, which reads woff2; on Windows it hands it to DirectWrite or GDI, which
read TrueType and OpenType only. And Qt keeps one file for each family, weight
and style: a second file at the same weight replaces the first instead of
filling in its missing characters, which on Windows would leave a subset's
characters to another face. So each weight is one file holding both subsets.

THE BRAND IS READ AT THE PIN, as tools/sync_colors.py reads it, and through
that tool's own check: a brand installed at another commit is refused.
Moving to a newer brand is: change the pin, install it, run both tools.

--check AND THE TEST NEED NO DECODER. They compare each brand file at the pin
with the sha256 fonts.json says its face was made from, each face with the
sha256 fonts.json records for it, and the licenses and fonts.json byte for
byte, but for line endings: a Windows checkout can turn LF into CRLF in a
text file, as tools/sync_colors.py allows for too. Writing a face needs fontTools and brotli (pip install fonttools
brotli); the tool says so when they are missing.

A file this tool wrote before and the brand no longer lists is named, and
--check fails on it; the tool deletes nothing. A file it did not write, such
as Montserrat-Black.ttf, is left alone.

THE SAME FILE IN EVERY APPLICATION. tests/test_fonts_in_sync.py runs the
--check half of this on every run, and utils/brand_fonts.py registers what
fonts.json names at startup, by file.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import io
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
FONTS = Path("resources") / "fonts"
MANIFEST = FONTS / "fonts.json"

#: The register's roles the interface uses. The mark is the bundled TTF.
ROLES = ("body", "mono")
#: The role whose license travels with the bundled TTF.
MARK = "mark"
#: The subset joined first, so its glyphs keep their own names.
FIRST_SUBSET = "latin"
_FACE_RULE = re.compile(r"@font-face \{(.*?)\}", re.S)


class SyncError(Exception):
    """The brand or this repository is not in a state the sync can read."""


def _sync_colors():
    """tools/sync_colors.py, loaded by path: tools/ is not a package. Its
    load_brand() reads rnv-brand at the pin, and refuses any other commit."""
    spec = importlib.util.spec_from_file_location("sync_colors", Path(__file__).with_name("sync_colors.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def license_name(family: str) -> str:
    """The register's name for a family's license file: OFL-Montserrat.txt."""
    return "OFL-" + family.replace(" ", "-") + ".txt"


def face_name(entry: dict) -> str:
    """The file a brand entry's weight goes into: inter-latin-ext-400-normal.woff2
    and inter-latin-400-normal.woff2 both go into inter-400-normal.ttf."""
    stem = entry["file"].rsplit(".", 1)[0]
    return stem.replace(f"-{entry['subset']}-", "-", 1) + ".ttf"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _subset_order(entry: dict) -> tuple[bool, str]:
    return (entry["subset"] != FIRST_SUBSET, entry["subset"])


def unicode_ranges(brand) -> dict[str, str]:
    """{brand file: its unicode-range}, as the brand's font_faces() declares them, in its order."""
    out: dict[str, str] = {}
    for rule in _FACE_RULE.findall(brand.font_faces("./")):
        file = re.search(r'url\("\./([^"]+)"\)', rule)
        spans = re.search(r"unicode-range:\s*([^;]+);", rule)
        if file is None or spans is None:
            raise SyncError("the brand's font_faces() declares a face with no file or no unicode-range")
        out[file.group(1)] = spans.group(1).strip()
    return out


def code_points(spans: str) -> list[tuple[int, int]]:
    """'U+0000-00FF,U+0131' as [(0x0, 0xFF), (0x131, 0x131)]."""
    out = []
    for part in spans.split(","):
        low, _, high = part.strip().removeprefix("U+").partition("-")
        out.append((int(low, 16), int(high or low, 16)))
    return out


def sources(root: Path = ROOT) -> tuple[str, dict[str, Any], dict[str, bytes], Path]:
    """What the brand holds at the pin: (pin, {role: plan}, {license path: bytes}, the brand's font folder).

    Each role's plan is {family, license, faces: [{file, weight, style, from: [{file, subset, sha256}]}]},
    faces in weight order, each face's sources with the Latin subset first."""
    colors = _sync_colors()
    try:
        brand, pin = colors.load_brand(root)
    except colors.SyncError as exc:
        raise SyncError(str(exc)) from exc
    source = Path(brand.fonts_dir())
    ranges = unicode_ranges(brand)
    declared = list(ranges)
    roles: dict[str, Any] = {}
    for role in ROLES:
        family = brand.TYPE[role]["family"]
        entries = [e for e in brand.font_files() if e["family"] == family]
        if not entries:
            raise SyncError(f"the brand lists no font file for TYPE[{role!r}], {family}")
        faces: dict[str, dict] = {}
        for entry in sorted(entries, key=_subset_order):
            face = faces.setdefault(face_name(entry), {"file": face_name(entry), "weight": str(entry["weight"]),
                                                       "style": entry["style"], "from": []})
            if entry["file"] not in ranges:
                raise SyncError(f"the brand's font_faces() does not declare {entry['file']}")
            face["from"].append({"file": entry["file"], "subset": entry["subset"],
                                 "sha256": sha256((source / entry["file"]).read_bytes()),
                                 "unicode_range": ranges[entry["file"]],
                                 "declared": declared.index(entry["file"])})
        ordered = sorted(faces.values(), key=lambda f: (int(f["weight"]), f["style"]))
        roles[role] = {"family": family, "license": license_name(family), "faces": ordered}
    licenses: dict[str, bytes] = {}
    for family in [brand.TYPE[role]["family"] for role in ROLES] + [brand.TYPE[MARK]["family"]]:
        path = source / license_name(family)
        if not path.is_file():
            raise SyncError(f"the brand has no {license_name(family)} for {family}")
        licenses[(FONTS / license_name(family)).as_posix()] = path.read_bytes()
    roles[MARK] = {"family": brand.TYPE[MARK]["family"], "license": license_name(brand.TYPE[MARK]["family"])}
    return pin, roles, licenses, source


def make_face(source: Path, parts: list[dict]) -> bytes:
    """One TrueType file from a weight's woff2 files: each decoded, then joined.

    `parts` are the face's "from" entries. Each file keeps only the characters
    its unicode-range gives it; a character in two ranges goes to the file
    the brand declared last.

    The woff2 files are fixed at the pin, and the result is the same bytes on
    every run of the same fontTools: the timestamp is kept from the sources,
    not set to now."""
    try:
        import brotli  # noqa: F401  fontTools reads woff2 through it
        from fontTools.merge import Merger
        from fontTools.ttLib import TTFont, woff2
    except ImportError as exc:
        raise SyncError("writing a face decodes the brand's woff2 files and joins their subsets with "
                        f"fontTools, which needs fonttools and brotli ({exc.name} is missing). "
                        "Run: pip install fonttools brotli") from exc
    spans = {p["file"]: code_points(p["unicode_range"]) for p in parts}

    def owner(code: int) -> str | None:
        claims = [p for p in parts if any(lo <= code <= hi for lo, hi in spans[p["file"]])]
        return max(claims, key=lambda p: p["declared"])["file"] if claims else None

    # A subset file maps characters outside its range: Latin Extended carries
    # its own A, under Amacron, and Latin some of Vietnamese. A browser never
    # draws those from it; joined, they would take the character from the
    # other file and leave its kerning and mark anchors on a glyph nothing
    # types. So each file keeps the characters its range gives it.
    decoded, heads = [], []
    for part in parts:
        raw = io.BytesIO()
        woff2.decompress(io.BytesIO((source / part["file"]).read_bytes()), raw)
        font = TTFont(io.BytesIO(raw.getvalue()))
        heads.append((font["head"].created, font["head"].modified))
        font.recalcTimestamp = False
        for table in font["cmap"].tables:
            table.cmap = {code: glyph for code, glyph in table.cmap.items() if owner(code) == part["file"]}
        out = io.BytesIO()
        font.save(out)
        out.seek(0)
        decoded.append(out)
    font = Merger().merge(decoded) if len(decoded) > 1 else TTFont(decoded[0])
    # The joiner stamps the file with the time it ran; keep the sources' own.
    font["head"].created = min(created for created, _ in heads)
    font["head"].modified = max(modified for _, modified in heads)
    font.recalcTimestamp = False
    _sort_layout(font)
    result = io.BytesIO()
    font.save(result)
    return result.getvalue()


def _sort_layout(font) -> None:
    """Put the joined GSUB and GPOS lists back in tag order, as the format asks.

    The joiner appends the second subset's features after the first's, so a
    feature tag can come after a later one; the OpenType Sanitizer, which
    browsers run on every web font, warns on that. Each language system's
    feature indices follow the features to their new places."""
    for tag in ("GSUB", "GPOS"):
        if tag not in font:
            continue
        table = font[tag].table
        if table.FeatureList and table.FeatureList.FeatureRecord:
            records = table.FeatureList.FeatureRecord
            order = sorted(range(len(records)), key=lambda i: (records[i].FeatureTag, i))
            moved = {old: new for new, old in enumerate(order)}
            table.FeatureList.FeatureRecord = [records[i] for i in order]
            for script in (table.ScriptList.ScriptRecord if table.ScriptList else []):
                systems = [script.Script.DefaultLangSys] + [r.LangSys for r in script.Script.LangSysRecord]
                for system in systems:
                    if system is None:
                        continue
                    system.FeatureIndex = sorted(moved[i] for i in system.FeatureIndex)
                    if system.ReqFeatureIndex != 0xFFFF:
                        system.ReqFeatureIndex = moved[system.ReqFeatureIndex]
            variations = getattr(table, "FeatureVariations", None)
            for rec in (variations.FeatureVariationRecord if variations else []):
                for sub in rec.FeatureTableSubstitution.SubstitutionRecord:
                    sub.FeatureIndex = moved[sub.FeatureIndex]
        if table.ScriptList:
            table.ScriptList.ScriptRecord.sort(key=lambda r: r.ScriptTag)
            for script in table.ScriptList.ScriptRecord:
                script.Script.LangSysRecord.sort(key=lambda r: r.LangSysTag)


def record(pin: str, roles: dict[str, Any], face_shas: dict[str, str]) -> dict[str, Any]:
    """fonts.json: the plan, with the sha256 of each face as written."""
    out_roles = {}
    for role in ROLES:
        plan = roles[role]
        files = [{"file": f["file"], "weight": f["weight"], "style": f["style"],
                  "sha256": face_shas.get(f["file"], ""), "from": f["from"]} for f in plan["faces"]]
        out_roles[role] = {"family": plan["family"], "license": plan["license"], "files": files}
    return {
        "about": "Written by tools/sync_fonts.py from rnv-brand at the commit pinned in "
                 "tests/requirements-dev.txt: each file is the brand's woff2 files for one weight, "
                 "decoded and joined, because Qt on Windows loads TrueType and OpenType only. "
                 "Don't edit it by hand: move the pin and run the tool. "
                 "utils/brand_fonts.py registers these files at startup.",
        "rnv_brand": pin,
        "roles": out_roles,
        "mark": {"family": roles[MARK]["family"], "license": roles[MARK]["license"],
                 "file": "Montserrat-Black.ttf"},
    }


def _encode(rec: dict[str, Any]) -> bytes:
    return (json.dumps(rec, indent=2) + "\n").encode("utf-8")


def _same_text(path: Path, data: bytes) -> bool:
    """The file holds `data`, with LF or with the CRLF a Windows checkout gives it."""
    if not path.is_file():
        return False
    raw = path.read_bytes()
    return raw == data or raw.replace(b"\r\n", b"\n") == data


def _on_disk(root: Path) -> dict[str, Any]:
    path = root / MANIFEST
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except ValueError:
        return {}


def written_before(root: Path = ROOT) -> set[str]:
    """The files the fonts.json on disk says this tool wrote."""
    old = _on_disk(root)
    names = {(FONTS / f["file"]).as_posix() for r in old.get("roles", {}).values() for f in r.get("files", [])}
    names |= {(FONTS / r["license"]).as_posix() for r in old.get("roles", {}).values() if "license" in r}
    if "license" in old.get("mark", {}):
        names.add((FONTS / old["mark"]["license"]).as_posix())
    return names


def _expected(roles: dict[str, Any], licenses: dict[str, bytes]) -> set[str]:
    return {(FONTS / f["file"]).as_posix() for role in ROLES for f in roles[role]["faces"]} | set(licenses)


def _stale_faces(root: Path, roles: dict[str, Any]) -> list[dict]:
    """The faces whose file, or whose record, is not what the brand at the pin makes."""
    recorded = {f["file"]: f for r in _on_disk(root).get("roles", {}).values() for f in r.get("files", [])}
    out = []
    for role in ROLES:
        for face in roles[role]["faces"]:
            path = root / FONTS / face["file"]
            mine = recorded.get(face["file"], {})
            if (not path.is_file() or mine.get("from") != face["from"]
                    or mine.get("weight") != face["weight"] or mine.get("style") != face["style"]
                    or sha256(path.read_bytes()) != mine.get("sha256")):
                out.append(face)
    return out


def _face_shas(root: Path, roles: dict[str, Any]) -> dict[str, str]:
    return {f["file"]: sha256((root / FONTS / f["file"]).read_bytes())
            for role in ROLES for f in roles[role]["faces"] if (root / FONTS / f["file"]).is_file()}


def stale(root: Path = ROOT) -> tuple[list[str], list[str]]:
    """(files out of date, files written before and no longer listed). Decodes nothing."""
    pin, roles, licenses, _source = sources(root)
    faces = _stale_faces(root, roles)
    out_of_date = [(FONTS / f["file"]).as_posix() for f in faces]
    out_of_date += [rel for rel, data in licenses.items() if not _same_text(root / rel, data)]
    if faces or not _same_text(root / MANIFEST, _encode(record(pin, roles, _face_shas(root, roles)))):
        out_of_date.append(MANIFEST.as_posix())
    return out_of_date, sorted(written_before(root) - _expected(roles, licenses))


def write(root: Path = ROOT) -> tuple[list[str], list[str]]:
    """Write what is out of date. (files written, files no longer listed)."""
    pin, roles, licenses, source = sources(root)
    left = sorted(written_before(root) - _expected(roles, licenses))
    written = []
    (root / FONTS).mkdir(parents=True, exist_ok=True)
    for face in _stale_faces(root, roles):
        (root / FONTS / face["file"]).write_bytes(make_face(source, face["from"]))
        written.append((FONTS / face["file"]).as_posix())
    for rel, data in licenses.items():
        if not _same_text(root / rel, data):
            (root / rel).write_bytes(data)
            written.append(rel)
    encoded = _encode(record(pin, roles, _face_shas(root, roles)))
    if not _same_text(root / MANIFEST, encoded):
        (root / MANIFEST).write_bytes(encoded)
        written.append(MANIFEST.as_posix())
    return written, left


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--check", action="store_true",
                        help="write nothing; exit 1 if a file is out of date")
    args = parser.parse_args(argv)
    try:
        if args.check:
            out_of_date, left = stale()
        else:
            written, left = write()
    except SyncError as exc:
        print(f"sync_fonts: {exc}", file=sys.stderr)
        return 2
    if args.check:
        for rel in out_of_date:
            print(f"out of date: {rel}")
        for rel in left:
            print(f"no longer listed by the brand: {rel}")
        if out_of_date or left:
            print("Run: python tools/sync_fonts.py")
            return 1
        print("in sync")
        return 0
    for rel in written:
        print(f"wrote {rel}")
    for rel in left:
        print(f"no longer listed by the brand, delete it by hand: {rel}")
    if not written:
        print("in sync; nothing to write")
    return 0


if __name__ == "__main__":
    sys.exit(main())
