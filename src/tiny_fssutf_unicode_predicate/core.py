"""Predicate for the Unicode FSS-UTF (UTF-8) encoding scheme.

FSS-UTF is the byte-oriented encoding now standardised as UTF-8. This module
decides whether a bytes-like value is a well-formed FSS-UTF sequence, and
reports the index of the first byte that breaks the scheme.

Why bytes and not str: the whole point of a byte-oriented predicate is that
it can be applied to data that may not decode. A Python ``str`` has already
survived decoding, so asking whether it is valid FSS-UTF is trivially true.
Accepting ``bytes``/``bytearray``/``memoryview`` lets callers validate wire
data before they commit to interpreting it.
"""

from __future__ import annotations

from typing import Union

BytesLike = Union[bytes, bytearray, memoryview]

__all__ = ["is_fssutf", "first_invalid_byte"]


def _as_bytes(data: BytesLike) -> bytes:
    """Normalise to ``bytes`` without copying when the input already is one.

    ``memoryview`` is the odd case: it is neither ``bytes`` nor ``bytearray``
    and cannot be indexed to an ``int`` unless its format is a byte format.
    Casting to ``bytes`` is the only portable way to get integer elements.
    """
    if isinstance(data, bytes):
        return data
    if isinstance(data, bytearray):
        return bytes(data)
    if isinstance(data, memoryview):
        return data.tobytes()
    raise TypeError(
        "expected bytes, bytearray, or memoryview, got %s" % type(data).__name__
    )


def first_invalid_byte(data: BytesLike) -> int:
    """Return the index of the first byte that violates FSS-UTF, or -1.

    The rules enforced are the ones in RFC 3629 / the Unicode standard:

    * A leading byte in ``0x00..0x7F`` is a one-byte sequence.
    * ``0xC2..0xDF`` introduces a two-byte sequence.
    * ``0xE0..0xEF`` introduces a three-byte sequence; ``0xE0`` may not be
      followed by ``0x80..0x9F`` (overlong), and ``0xED`` may not be followed
      by ``0xA0..0xBF`` (surrogate range).
    * ``0xF0..0xF4`` introduces a four-byte sequence; ``0xF0`` may not be
      followed by ``0x80..0x8F`` (overlong), and ``0xF4`` may not be followed
      by ``0x90..0xBF`` (above U+10FFFF).
    * Continuation bytes are ``0x80..0xBF``.
    * ``0xC0``, ``0xC1``, and ``0xF5..0xFF`` are never legal leading bytes.

    The overlong and range checks are performed on the *second* byte only,
    because that is where the leading byte's contribution is bounded; the
    remaining continuation bytes are unconstrained within ``0x80..0xBF``.
    """
    buf = _as_bytes(data)
    n = len(buf)
    i = 0
    while i < n:
        b0 = buf[i]
        if b0 <= 0x7F:
            i += 1
            continue
        if 0xC2 <= b0 <= 0xDF:
            need = 1
            lo, hi = 0x80, 0xBF
        elif 0xE0 <= b0 <= 0xEF:
            need = 2
            if b0 == 0xE0:
                lo, hi = 0xA0, 0xBF
            elif b0 == 0xED:
                lo, hi = 0x80, 0x9F
            else:
                lo, hi = 0x80, 0xBF
        elif 0xF0 <= b0 <= 0xF4:
            need = 3
            if b0 == 0xF0:
                lo, hi = 0x90, 0xBF
            elif b0 == 0xF4:
                lo, hi = 0x80, 0x8F
            else:
                lo, hi = 0x80, 0xBF
        else:
            return i
        if i + need >= n:
            return i
        b1 = buf[i + 1]
        if not (lo <= b1 <= hi):
            return i
        for k in range(2, need + 1):
            if not (0x80 <= buf[i + k] <= 0xBF):
                return i + k
        i += need + 1
    return -1


def is_fssutf(data: BytesLike) -> bool:
    """Return ``True`` if ``data`` is a well-formed FSS-UTF byte sequence.

    Empty input is valid: the empty sequence encodes the empty string.
    """
    return first_invalid_byte(data) == -1
