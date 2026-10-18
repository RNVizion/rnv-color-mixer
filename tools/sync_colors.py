"""Write this application's colours from the brand.   RNV-COLOUR-SYNC, 2026-10-16

    python tools/sync_colors.py           write the colour file and COLORS.md
    python tools/sync_colors.py --check   write nothing; exit 1 if either is out of date

brand_map.json, at the repository root, says where each colour in the colour
file it names comes from: a name in rnv-brand, such as "APP.card", or a value
this application owns, with the reason. This script writes the value on each
of those lines, and COLORS.md, the chart of this application's colours.

THE BRAND IS READ AT THE PIN. A brand name's value comes from rnv-brand as
installed, and only when that is the commit pinned in
tests/requirements-dev.txt, so what is written is what this repository
declares, never whatever happens to be installed. Moving to a newer brand is:
change the pin, `pip install -r tests/requirements-dev.txt`, run this script,
and read the diff of the colour file. It shows exactly what moved.
.github/workflows/brand-sync.yml does that every day, and opens a pull
request only when a colour this application uses has moved.

NOTHING READS THE BRAND WHILE THE APPLICATION RUNS. The values are written
into the source and the build carries them. A derived colour, such as
lighten(BRAND_GOLD, 13), stays code in the colour file and follows its base.
Image files are not touched.

THE SAME FILE IN EVERY APPLICATION. What differs between them is in
brand_map.json: the colour file, the palettes the chart reads, and the map.

tests/test_colours_in_sync.py runs the --check half of this on every run.
"""
from __future__ import annotations

import argparse
import ast
import importlib.metadata
import io
import json
import re
import sys
import tokenize
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent

#: Where this repository pins the register.
DEV_REQS = "tests/requirements-dev.txt"

#: The register's tables a map entry may name, as TABLE.key. A name with no
#: table, such as GOLD_TEXT_GROUND_FLOOR, is one of the register's own
#: constants.
TABLES = ("PERMANENT", "APP", "STATUS")

#: The same pin tests/test_register_pin.py reads: a full commit, never a branch.
PIN_RE = re.compile(
    r"^rnv-brand\s*@\s*git\+https://github\.com/RNVizion/rnv-brand"
    r"(?:\.git)?@(?P<ref>[0-9a-f]{40})\s*$", re.M)

#: One colour constant on one line, `NAME = <value>` or `NAME: <type> = <value>`,
#: with the marker this script writes at the end, or none before its first run.
LINE_RE = (r"^(?P<head>{name}(?:\s*:[^=]+?)?\s*=\s*)(?P<value>.+?)"
           r"(?P<mark>  # (?:brand: \S+|app-owned))?$")
MARK_RE = re.compile(r"  # (?:brand: \S+|app-owned)$")

_HEX_RE = re.compile(r"#[0-9a-fA-F]{6}(?:[0-9a-fA-F]{2})?")
_RGBA_RE = re.compile(r"rgba?\([\d\s,.]+\)")
_NAME_RE = re.compile(r"[A-Z][A-Z0-9_]*")


class SyncError(Exception):
    """Something this script will not write past. The message says what to do."""


# ------------------------------------------------------------------- files

def read(path: Path) -> tuple[str, tuple[bool, bool]]:
    """A file as text with LF endings, and its form: (a byte-order mark, CRLF
    throughout). An edit must not change the bytes it did not mean to."""
    raw = path.read_bytes()
    bom = raw.startswith(b"\xef\xbb\xbf")
    text = (raw[3:] if bom else raw).decode("utf-8")
    crlf = text.count("\r\n")
    all_crlf = crlf > 0 and crlf == text.count("\n")
    return (text.replace("\r\n", "\n") if all_crlf else text), (bom, all_crlf)


def write(path: Path, text: str, form: tuple[bool, bool] = (False, False)) -> None:
    bom, all_crlf = form
    if all_crlf:
        text = text.replace("\n", "\r\n")
    path.write_bytes((b"\xef\xbb\xbf" if bom else b"") + text.encode("utf-8"))


# ------------------------------------------------------------------ the map

def load_map(root: Path = ROOT) -> dict[str, Any]:
    """brand_map.json, checked entry by entry before anything is written."""
    data = json.loads((root / "brand_map.json").read_text(encoding="utf-8"))
    colours = data.get("colours")
    if not isinstance(colours, dict) or not colours:
        raise SyncError("brand_map.json has no colours")
    if not isinstance(data.get("colour_file"), str):
        raise SyncError("brand_map.json does not name its colour_file")
    for name, entry in colours.items():
        if isinstance(entry, str):
            table, dot, key = entry.partition(".")
            if dot and (table not in TABLES or not key):
                raise SyncError(f"{name}: {entry!r} is not TABLE.key, with TABLE "
                                f"one of {', '.join(TABLES)}")
            if not dot and not _NAME_RE.fullmatch(entry):
                raise SyncError(f"{name}: {entry!r} is neither TABLE.key nor one of "
                                f"the register's constants")
        elif isinstance(entry, dict):
            if set(entry) != {"app", "why"}:
                raise SyncError(f"{name}: an app-owned colour is "
                                f'{{"app": <value>, "why": <reason>}}')
            if not isinstance(entry["why"], str) or not entry["why"].strip():
                raise SyncError(f"{name}: an app-owned colour needs its reason")
            if not is_colour(_as_python(entry["app"])):
                raise SyncError(f"{name}: {entry['app']!r} is not a colour")
        else:
            raise SyncError(f"{name}: an entry is a brand name or an app-owned object")
    return data


def _as_python(value: Any) -> Any:
    """A map value as Python holds it: JSON has no tuples."""
    return tuple(value) if isinstance(value, list) else value


def is_colour(value: Any) -> bool:
    """A hex, an rgb()/rgba() string, or an (r, g, b[, a]) tuple of bytes."""
    if isinstance(value, str):
        return bool(_HEX_RE.fullmatch(value) or _RGBA_RE.fullmatch(value))
    if isinstance(value, tuple):
        return len(value) in (3, 4) and all(
            isinstance(c, int) and not isinstance(c, bool) and 0 <= c <= 255
            for c in value)
    return False


# ---------------------------------------------------------------- the brand

def pinned_commit(root: Path = ROOT) -> str:
    """The rnv-brand commit tests/requirements-dev.txt pins."""
    match = PIN_RE.search((root / DEV_REQS).read_text(encoding="utf-8"))
    if not match:
        raise SyncError(f"{DEV_REQS} does not pin rnv-brand to a full commit")
    return match.group("ref")


def installed_commit() -> str | None:
    """The commit pip recorded when it installed rnv-brand, if it did."""
    try:
        dist = importlib.metadata.distribution("rnv-brand")
    except importlib.metadata.PackageNotFoundError:
        return None
    raw = dist.read_text("direct_url.json")
    if not raw:
        return None
    return json.loads(raw).get("vcs_info", {}).get("commit_id")


def load_brand(root: Path = ROOT) -> tuple[Any, str]:
    """engine.brand, refused unless it is the pinned commit."""
    pin = pinned_commit(root)
    have = installed_commit()
    if have != pin:
        raise SyncError(
            f"the rnv-brand installed here is "
            f"{have[:7] if have else 'not one pip recorded a commit for'}, and "
            f"this repository pins {pin[:7]}. "
            f"Run: pip install -r {DEV_REQS}")
    import engine.brand as brand
    return brand, pin


def brand_value(brand: Any, ref: str) -> str:
    """The value a brand name holds in the register, in lower case."""
    table, dot, key = ref.partition(".")
    if dot:
        values = getattr(brand, table, None)
        if not isinstance(values, dict) or key not in values:
            raise SyncError(f"rnv-brand has no {ref}")
        value = values[key]
    else:
        if not hasattr(brand, ref):
            raise SyncError(f"rnv-brand has no {ref}")
        value = getattr(brand, ref)
    if not (isinstance(value, str) and re.fullmatch(r"#[0-9a-fA-F]{6}", value)):
        raise SyncError(f"{ref} is {value!r}, not a six-digit hex colour")
    return value.lower()


# ----------------------------------------------------------- the colour file

def spell(value: Any, like: str = '"') -> str:
    """A value as the colour file writes it, in the quotes the line already uses."""
    if isinstance(value, str):
        if like.startswith("'") and "'" not in value:
            return f"'{value}'"
        return json.dumps(value)
    return "(" + ", ".join(str(c) for c in value) + ")"


def resolve(mapping: dict[str, Any], brand: Any) -> dict[str, tuple[Any, str]]:
    """Each mapped name: (its value, the marker its line carries)."""
    out: dict[str, tuple[Any, str]] = {}
    for name, entry in mapping["colours"].items():
        if isinstance(entry, str):
            out[name] = (brand_value(brand, entry), f"brand: {entry}")
        else:
            out[name] = (_as_python(entry["app"]), "app-owned")
    return out


def colour_constants(text: str) -> list[str]:
    """Every module-level constant written as a colour literal."""
    names = []
    for node in ast.parse(text).body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)) or node.value is None:
            continue
        target = node.targets[0] if isinstance(node, ast.Assign) else node.target
        if not isinstance(target, ast.Name):
            continue
        try:
            value = ast.literal_eval(node.value)
        except ValueError:
            continue
        if is_colour(value):
            names.append(target.id)
    return names


def rewrite(text: str, resolved: dict[str, tuple[Any, str]], where: str) -> str:
    """The colour file with every mapped line written from the map."""
    lines = text.split("\n")
    for name, (value, mark) in resolved.items():
        pattern = re.compile(LINE_RE.format(name=re.escape(name)))
        hits = [i for i, line in enumerate(lines) if pattern.match(line)]
        if len(hits) != 1:
            raise SyncError(f"{where}: expected one line defining {name}, "
                            f"found {len(hits)}")
        match = pattern.match(lines[hits[0]])
        tokens = tokenize.generate_tokens(io.StringIO(match.group("value")).readline)
        if any(token.type == tokenize.COMMENT for token in tokens):
            raise SyncError(
                f"{where}: {name}'s line carries a comment the sync would drop. "
                f"Move it to the line above; the sync writes the line's marker.")
        try:
            ast.literal_eval(match.group("value"))
        except (ValueError, SyntaxError):
            raise SyncError(
                f"{where}: {name} is written as {match.group('value')!r}, which is "
                f"code, not a value. A derived colour stays code; take {name} "
                f"out of brand_map.json.") from None
        lines[hits[0]] = (f"{match.group('head')}{spell(value, match.group('value'))}"
                          f"  # {mark}")
    new = "\n".join(lines)
    unmapped = [n for n in colour_constants(new) if n not in resolved]
    if unmapped:
        raise SyncError(
            f"{where} writes colours brand_map.json does not hold: "
            f"{', '.join(unmapped)}. Add each, as a brand name or as app-owned "
            f"with its reason.")
    return new


# ------------------------------------------------------------------ the chart

def _shown(value: Any) -> str:
    return value if isinstance(value, str) else "(" + ", ".join(map(str, value)) + ")"


def _cell(text: str) -> str:
    return text.replace("|", "\\|")


def _module_namespace(text: str, path: Path, root: Path) -> dict[str, Any]:
    """The colour file's names, as it defines them from this text."""
    module = ".".join(path.relative_to(root).with_suffix("").parts)
    namespace: dict[str, Any] = {"__file__": str(path), "__name__": module}
    added = str(root) not in sys.path
    if added:
        sys.path.insert(0, str(root))
    try:
        exec(compile(text, str(path.relative_to(root)), "exec"), namespace)
    finally:
        if added:
            sys.path.remove(str(root))
    return namespace


def _palettes(text: str, mapping: dict[str, Any], root: Path) -> list[tuple[str, str, ast.Dict]]:
    """(locator, label, dict display) for each palette the chart reads."""
    wanted = mapping.get("palettes")
    found = []
    if wanted is None:
        for node in ast.parse(text).body:
            if (isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name)
                    and isinstance(node.value, ast.Dict)
                    and ast.unparse(node.annotation) == "Final[ThemeDict]"):
                found.append((node.target.id, node.value))
    else:
        for entry in wanted:
            source = (text if entry["file"] == mapping["colour_file"]
                      else read(root / entry["file"])[0])
            body = ast.parse(source).body
            *owner, name = entry["dict"].split(".")
            for part in owner:
                body = next(n for n in body if isinstance(n, ast.ClassDef) and n.name == part).body
            node = next(n for n in body if isinstance(n, (ast.Assign, ast.AnnAssign))
                        and getattr(n.targets[0] if isinstance(n, ast.Assign) else n.target,
                                    "id", None) == name)
            found.append((entry["dict"], node.value))
    out = []
    for locator, node in found:
        label = next((v.value for k, v in zip(node.keys, node.values)
                      if isinstance(k, ast.Constant) and k.value == "name"
                      and isinstance(v, ast.Constant)), locator.split(".")[-1].title())
        out.append((locator, label, node))
    return out


def chart(text: str, mapping: dict[str, Any], brand: Any, pin: str, root: Path = ROOT) -> str:
    """COLORS.md: the brand's names, their values, and this application's names."""
    colour_path = root / mapping["colour_file"]
    namespace = _module_namespace(text, colour_path, root)
    tree = ast.parse(text)
    colours = mapping["colours"]

    source: dict[str, str] = {}
    for node in tree.body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)) or node.value is None:
            continue
        target = node.targets[0] if isinstance(node, ast.Assign) else node.target
        if isinstance(target, ast.Name) and is_colour(namespace.get(target.id)):
            source[target.id] = ast.unparse(node.value)

    # A derived colour is made from the colour names its expression reads.
    derived = [n for n in source if n not in colours]
    reads = {n: {x.id for x in ast.walk(ast.parse(source[n], mode="eval"))
                 if isinstance(x, ast.Name) and x.id in source} for n in derived}

    def roots(name: str, seen: frozenset[str] = frozenset()) -> set[str]:
        if name in colours:
            return {name}
        out: set[str] = set()
        for base in reads.get(name, ()):
            if base not in seen:
                out |= roots(base, seen | {name})
        return out

    made_from: dict[str, list[str]] = {n: [] for n in colours}
    for name in derived:
        for base in sorted(roots(name)):
            made_from[base].append(name)

    def made(name: str) -> str:
        return "<br>".join(
            f"`{d}` = `{_cell(source[d])}` → `{_shown(namespace[d])}`"
            for d in made_from[name]) or "—"

    def brand_order(item: tuple[str, Any]) -> tuple[int, int]:
        table, dot, key = item[1].partition(".")
        if not dot:
            return len(TABLES), 0
        keys = list(getattr(brand, table))
        return TABLES.index(table), keys.index(key)

    from_brand = sorted(((n, e) for n, e in colours.items() if isinstance(e, str)),
                        key=brand_order)
    own = [(n, e) for n, e in colours.items() if isinstance(e, dict)]
    orphans = [n for n in derived if not roots(n)]

    out = [
        f"# Colours: {mapping.get('app', 'this application')}",
        "",
        f"Generated by `python tools/sync_colors.py` from `brand_map.json`, "
        f"`{mapping['colour_file']}` and rnv-brand at `{pin[:7]}`, the commit pinned in "
        f"`{DEV_REQS}`. Don't edit it by hand: change the map and run "
        f"the script. `tests/test_colours_in_sync.py` fails when this file is out of date.",
        "",
        f"{len(from_brand)} colours come from the brand and {len(own)} are the "
        f"application's own. {len(derived)} more are worked out in "
        f"`{mapping['colour_file']}` from those, so they follow them.",
        "",
        "## From the brand",
        "",
        "| brand name | value | the app's name | made from it in the app |",
        "|---|---|---|---|",
    ]
    for name, ref in from_brand:
        out.append(f"| `{ref}` | `{_shown(namespace[name])}` | `{name}` | {made(name)} |")
    out += [
        "",
        "## The application's own",
        "",
        "| the app's name | value | why | made from it in the app |",
        "|---|---|---|---|",
    ]
    for name, entry in own:
        out.append(f"| `{name}` | `{_shown(namespace[name])}` | {_cell(entry['why'])} "
                   f"| {made(name)} |")
    if orphans:
        out += ["", "Worked out from no colour above: "
                + ", ".join(f"`{n}`" for n in orphans) + "."]

    # Each palette's keys, in order: the expression it writes, or "as dark"
    # where it takes the entry from a palette it spreads.
    out += ["", "## What each palette key takes", ""]
    palettes = _palettes(text, mapping, root)
    entries: dict[str, dict[str, str]] = {}
    labels: dict[str, str] = {}
    for locator, label, node in palettes:
        written: dict[str, str] = {}
        for key, value in zip(node.keys, node.values):
            if key is None:
                spread = ast.unparse(value).split(".")[-1]
                base = next(l for l in entries if l.split(".")[-1] == spread)
                written.update({k: f"as {labels[base].lower()}" for k in entries[base]})
            elif isinstance(key, ast.Constant) and key.value != "name":
                written[key.value] = ast.unparse(value)
        entries[locator] = written
        labels[locator] = label
    out.append("| key | " + " | ".join(labels[l] for l in entries) + " |")
    out.append("|---|" + "---|" * len(entries))
    keys: list[str] = []
    for written in entries.values():
        keys += [k for k in written if k not in keys]
    for key in keys:
        cells = []
        for locator, written in entries.items():
            expr = written.get(key)
            if expr is None:
                cells.append("—")
                continue
            if expr.startswith("as "):
                cells.append(expr)
                continue
            try:
                value = eval(expr, dict(namespace))
            except Exception:
                cells.append(f"`{_cell(expr)}`")
                continue
            if not isinstance(value, (str, tuple)) or not (is_colour(value) or isinstance(value, str)):
                cells.append(f"`{_cell(expr)}`")
            elif expr == repr(value):
                cells.append(f"`{_shown(value)}`")
            else:
                cells.append(f"`{_cell(expr)}` `{_shown(value)}`")
        out.append(f"| `{key}` | " + " | ".join(cells) + " |")
    notes = mapping.get("notes") or []
    if notes:
        out += ["", "## Not in the map", ""] + [f"- {_cell(n)}" for n in notes]
    out += ["", "Which widgets each key reaches is in the fleet chart, *RNV Colour Chart*.", ""]
    return "\n".join(out)


# --------------------------------------------------------------------- run it

def build(root: Path = ROOT) -> dict[Path, tuple[str, str, tuple[bool, bool]]]:
    """Each file this script owns: (what is there, what it would write, its form)."""
    mapping = load_map(root)
    brand, pin = load_brand(root)
    colour_path = root / mapping["colour_file"]
    before, form = read(colour_path)
    after = rewrite(before, resolve(mapping, brand), mapping["colour_file"])
    chart_path = root / "COLORS.md"
    chart_before, chart_form = read(chart_path) if chart_path.exists() else ("", (False, False))
    return {colour_path: (before, after, form),
            chart_path: (chart_before, chart(after, mapping, brand, pin, root), chart_form)}


def moved(before: str, after: str) -> list[str]:
    """What a write changed: each value that moved, and how many lines only
    gained their marker."""
    changes, marked = [], 0
    for a, b in zip(before.split("\n"), after.split("\n")):
        if a == b:
            continue
        old, new = MARK_RE.sub("", a), MARK_RE.sub("", b)
        if old == new:
            marked += 1
            continue
        name = re.split(r"\s*[:=]", new, maxsplit=1)[0]
        changes.append(f"  {name}: {re.split(r' = ', old, maxsplit=1)[-1]} -> "
                       f"{re.split(r' = ', new, maxsplit=1)[-1]}")
    if marked:
        changes.append(f"  {marked} line(s) marked, no value moved")
    return changes


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--check", action="store_true",
                        help="write nothing; exit 1 if a file is out of date")
    args = parser.parse_args(argv)
    try:
        plan = build()
    except SyncError as exc:
        print(f"sync_colors: {exc}", file=sys.stderr)
        return 2
    stale = [path for path, (before, after, _form) in plan.items() if before != after]
    if args.check:
        for path in stale:
            print(f"out of date: {path.relative_to(ROOT).as_posix()}")
        if stale:
            print("Run: python tools/sync_colors.py")
            return 1
        print("in sync")
        return 0
    for path in stale:
        before, after, form = plan[path]
        write(path, after, form)
        print(f"wrote {path.relative_to(ROOT).as_posix()}")
        if path.suffix == ".py":
            print("\n".join(moved(before, after)))
    if not stale:
        print("in sync; nothing to write")
    return 0


if __name__ == "__main__":
    sys.exit(main())
