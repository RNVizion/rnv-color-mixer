"""ATOMIC WRITES FOR THE FILES THE APPLICATION KEEPS FOR ITSELF (#83 A, 2026-10-22).

The same file in all five RNV desktop applications.

THE FAULT IT KEEPS AWAY. A settings, session, history or preset file was
written in place: open(path, "w") truncates the file first, then the new
content follows. A crash, a kill or a full disk between those two steps
leaves an empty or half-written file, and the next start reads it as
corrupt, or as nothing. The picker's color history was already written this
way; the other state files were not.

HOW. The content is serialized first, in memory, so a value that cannot be
written is refused before any file is touched. It is then written to a
temporary file beside the target, named <name>.<pid>-<thread>-<n>.tmp and created
exclusively, flushed and fsynced, and os.replace() swaps it in. The replace
is atomic on Windows and POSIX alike: a reader sees the old file or the new
one, never a mixture. On failure the temporary file is removed and the old
file is left as it was.

WHY A REFUSED REPLACE IS TRIED AGAIN. Windows refuses a replace onto a file
for a moment while another replace onto it is still finishing, with
PermissionError ("Access is denied"); an indexer or a virus scanner holding
the file does the same. Linux never does. Seen on Chris's machine on
2026-10-23, in the guard that runs two writers on one file. The replace is
tried again, waiting 1, 2, 4 ... 512 ms between tries (about a second in
all), and only then does the error stand.

WHY THE TEMPORARY NAME IS UNIQUE. The mixer's history keeps a retired writer
thread running beside the current one, and two writers sharing one
<name>.tmp raced: the second truncated the first's file and then found it
gone. Each write has its own temporary file, and the last replace wins with
a whole file.

WHAT IT DOES NOT DO. It does not create directories; a caller that needs
one makes it first, as before. It writes bytes, so a text file always ends
its lines with a line feed. Exports the user asks for (PNG, CSS, JSON the
user names) are not state and keep their own writers.

tests/test_atomic_state_writes.py holds every state writer to these three
functions.
"""
from __future__ import annotations

import itertools
import json
import os
import threading
import time
from pathlib import Path
from typing import Any

__all__ = ["atomic_write_bytes", "atomic_write_text", "atomic_write_json"]

_counter = itertools.count()

#: seconds to wait before each new try of a refused replace
RETRY_DELAYS = tuple(0.001 * 2 ** i for i in range(10))


def _temp_name(target: Path) -> Path:
    """A name beside target that no other write in this process is using."""
    return target.with_name(f"{target.name}.{os.getpid()}-{threading.get_ident()}-{next(_counter)}.tmp")


def atomic_write_bytes(path: str | os.PathLike[str], data: bytes) -> None:
    """Write data to path so that the file is either the old one or the new one."""
    target = Path(path)
    temp = _temp_name(target)
    try:
        with open(temp, "xb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        _replace(temp, target)
    except BaseException:
        try:
            temp.unlink()
        except OSError:
            pass
        raise


def _replace(temp: Path, target: Path) -> None:
    """os.replace(), tried again while Windows refuses it for a moment."""
    for delay in RETRY_DELAYS:
        try:
            os.replace(temp, target)
            return
        except PermissionError:
            time.sleep(delay)
    os.replace(temp, target)


def atomic_write_text(path: str | os.PathLike[str], text: str, encoding: str = "utf-8") -> None:
    """Encode text and write it atomically."""
    atomic_write_bytes(path, text.encode(encoding))


def atomic_write_json(path: str | os.PathLike[str], data: Any, **dump_kwargs: Any) -> None:
    """Serialize data with json.dumps(**dump_kwargs) and write it atomically.

    A value json cannot serialize raises before any file is touched.
    """
    atomic_write_text(path, json.dumps(data, **dump_kwargs))
