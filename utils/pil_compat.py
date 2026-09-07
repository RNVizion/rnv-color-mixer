"""Pillow compatibility -- one API that moved under us, in one place.

WHY THIS FILE EXISTS. `Image.getdata()` was deprecated in Pillow 12.1 and will
be REMOVED in Pillow 14, dated 2027-10-15. The deprecation names
`get_flattened_data()` as its replacement.

The obvious fix -- swap the call -- breaks this application today, because
`get_flattened_data` does not exist before Pillow 12.1 and this project
supports Pillow 10. Measured rather than assumed:

    Pillow 10.4.0   get_flattened_data absent    getdata not deprecated
    Pillow 11.0.0   absent                       not deprecated
    Pillow 11.3.0   absent                       not deprecated
    Pillow 12.0.0   absent                       not deprecated
    Pillow 12.1.0   PRESENT                      DEPRECATED
    Pillow 12.2.0   present                      deprecated

So the call has to ask which Pillow it is running on. Asking once, here, is
better than asking at each call site: there were five of them across three
applications, and the next person to add a sixth will not know to ask.

The two are behaviourally identical -- same length, same tuples, same palette
indices -- verified on RGB, RGBA, L and P in tests/test_pil_compat.py.
"""
from __future__ import annotations

from typing import Any


def flat_pixels(image: Any) -> list:
    """Every pixel of `image`, in row-major order.

    The replacement for `list(image.getdata())`. Returns exactly what that
    returned: RGB and RGBA give tuples, L gives ints, P gives palette indices.

    `getattr` rather than a version comparison on purpose. A version string
    answers "which Pillow is this", which is a proxy for the question actually
    being asked -- "does this object have the method" -- and the proxy is wrong
    for anyone running a fork, a pre-release, or a vendored build.
    """
    getter = getattr(image, "get_flattened_data", None)
    return list(getter() if getter is not None else image.getdata())
