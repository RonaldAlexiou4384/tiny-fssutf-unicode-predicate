import unittest

from tiny_fssutf_unicode_predicate import first_invalid_byte, is_fssutf


class TestIsFssutf(unittest.TestCase):
    def test_empty_is_valid(self):
        self.assertTrue(is_fssutf(b""))
        self.assertEqual(first_invalid_byte(b""), -1)

    def test_ascii(self):
        self.assertTrue(is_fssutf(b"hello, world"))
        self.assertTrue(is_fssutf(b"\x00\x7f"))

    def test_two_byte(self):
        self.assertTrue(is_fssutf("\u00e9".encode("utf-8")))
        self.assertTrue(is_fssutf("\u07ff".encode("utf-8")))

    def test_three_byte(self):
        self.assertTrue(is_fssutf("\u0800".encode("utf-8")))
        self.assertTrue(is_fssutf("\uffff".encode("utf-8")))

    def test_four_byte(self):
        self.assertTrue(is_fssutf("\U00010000".encode("utf-8")))
        self.assertTrue(is_fssutf("\U0010ffff".encode("utf-8")))

    def test_accepts_bytearray_and_memoryview(self):
        raw = "caf\u00e9".encode("utf-8")
        self.assertTrue(is_fssutf(bytearray(raw)))
        self.assertTrue(is_fssutf(memoryview(raw)))

    def test_rejects_non_bytes(self):
        with self.assertRaises(TypeError):
            is_fssutf("caf\u00e9")  # type: ignore[arg-type]

    def test_lone_continuation_byte(self):
        self.assertFalse(is_fssutf(b"\x80"))
        self.assertEqual(first_invalid_byte(b"\x80"), 0)

    def test_truncated_sequence(self):
        self.assertEqual(first_invalid_byte(b"\xc3"), 0)
        self.assertEqual(first_invalid_byte(b"\xe2\x82"), 0)
        self.assertEqual(first_invalid_byte(b"\xf0\x9f\x98"), 0)

    def test_overlong_two_byte(self):
        # 0xC0/0xC1 are always illegal leading bytes.
        self.assertEqual(first_invalid_byte(b"\xc0\xaf"), 0)
        self.assertEqual(first_invalid_byte(b"\xc1\xbf"), 0)

    def test_overlong_three_byte(self):
        # 0xE0 0x80 0x80 encodes U+0000 in overlong form.
        self.assertEqual(first_invalid_byte(b"\xe0\x80\x80"), 0)
        self.assertEqual(first_invalid_byte(b"\xe0\x9f\xbf"), 0)
        self.assertTrue(is_fssutf(b"\xe0\xa0\x80"))

    def test_surrogate_range_rejected(self):
        # 0xED 0xA0 0x80 would be U+D800, which FSS-UTF forbids.
        self.assertEqual(first_invalid_byte(b"\xed\xa0\x80"), 0)
        self.assertTrue(is_fssutf(b"\xed\x9f\xbf"))

    def test_overlong_four_byte(self):
        self.assertEqual(first_invalid_byte(b"\xf0\x80\x80\x80"), 0)
        self.assertEqual(first_invalid_byte(b"\xf0\x8f\xbf\xbf"), 0)
        self.assertTrue(is_fssutf(b"\xf0\x90\x80\x80"))

    def test_above_unicode_max(self):
        # 0xF4 0x90 0x80 0x80 is U+110000.
        self.assertEqual(first_invalid_byte(b"\xf4\x90\x80\x80"), 0)
        self.assertTrue(is_fssutf(b"\xf4\x8f\xbf\xbf"))

    def test_illegal_leading_bytes(self):
        for b in (0xF5, 0xF6, 0xFA, 0xFE, 0xFF):
            self.assertEqual(first_invalid_byte(bytes([b])), 0)

    def test_bad_continuation_reports_its_index(self):
        # Second byte is fine; the third is not a continuation byte.
        self.assertEqual(first_invalid_byte(b"\xe2\x82A"), 2)

    def test_error_index_after_valid_prefix(self):
        self.assertEqual(first_invalid_byte(b"ab\xffcd"), 2)

    def test_round_trip_of_a_real_string(self):
        sample = "\u00e9\u20ac\U0001f600 \u4e2d\u6587"
        self.assertTrue(is_fssutf(sample.encode("utf-8")))


if __name__ == "__main__":
    unittest.main()
