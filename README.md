# tiny-fssutf-unicode-predicate

Decide whether a byte sequence is well-formed FSS-UTF (UTF-8), and find the
first byte that breaks the rules.

```python
from tiny_fssutf_unicode_predicate import is_fssutf, first_invalid_byte

is_fssutf("caf\u00e9".encode("utf-8"))   # True
is_fssutf(b"\xc3")                       # False, truncated
first_invalid_byte(b"ab\xffcd")          # 2
```

Both functions accept `bytes`, `bytearray`, or `memoryview`. Anything else
raises `TypeError`.

## Why this exists

Python already has `bytes.decode("utf-8")`, which raises on bad input, so a
predicate looks redundant. The reason to have one is that decoding conflates
two questions: *is this valid?* and *what does it say?* When you are looking
at a packet, a log line, or a file whose encoding you do not yet trust, you
want the first answer without paying for the second, and you want the offset
of the offending byte so you can say something useful about it.

`first_invalid_byte` returns that offset, or `-1` when the whole input is
valid. `is_fssutf` is the boolean wrapper.

The trade-off: this is a hand-written byte scanner, not a wrapper around the
C decoder. It is slower than `str.decode` and it deliberately rejects the
five- and six-byte forms from the original 1992 FSS-UTF proposal, because the
Unicode standard dropped them. If you need to accept those legacy forms, this
library is not for you.

## The awkward edge

`first_invalid_byte` reports the index of the *leading* byte of a malformed
sequence when the sequence is truncated or has a bad second byte, but the
index of the bad *continuation* byte when a later continuation is wrong. For
example `first_invalid_byte(b"\xe2\x82")` is `0` (there is no third byte),
while `first_invalid_byte(b"\xe2\x82A")` is `2`. That is the byte you would
point at in a hex dump, which is what the function is for.
