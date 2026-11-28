import tempfile
from pathlib import Path
import unittest
from trim import trim


class TrimTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.src = Path(tmp.name) / 'source.txt'
        self.dst = Path(tmp.name) / 'out.txt'

    def check_conversion(self, original, expected):
        self.src.write_bytes(original)
        trim(self.src, self.dst)
        self.assertEqual(self.dst.read_bytes(), expected)
        self.assertEqual(self.src.read_bytes(), original)

    def test_mixed_endings_and_final_line(self):
        self.check_conversion(b'a \r\nb\t\nc \r d \t', b'a\r\nb\nc\r d')

    def test_empty(self):
        self.check_conversion(b'', b'')

    def test_whitespace_only(self):
        self.check_conversion(b' \t\n\t', b'\n')

    def test_utf8_and_bom(self):
        self.check_conversion('\ufeff日本語 \t\r\nあ\u3000 \n'.encode(),
                              '\ufeff日本語\r\nあ\u3000\n'.encode())

    def test_existing_output(self):
        self.src.write_bytes(b'input ')
        self.dst.write_bytes(b'human output')
        with self.assertRaises(FileExistsError):
            trim(self.src, self.dst)
        self.assertEqual(self.dst.read_bytes(), b'human output')

    def test_same_input_output(self):
        self.src.write_bytes(b'input ')
        with self.assertRaises(FileExistsError):
            trim(self.src, self.src)
        self.assertEqual(self.src.read_bytes(), b'input ')

    def test_invalid_utf8(self):
        self.src.write_bytes(b'\xff')
        with self.assertRaises(UnicodeError):
            trim(self.src, self.dst)
        self.assertFalse(self.dst.exists())

    def test_existing_output_link(self):
        self.src.write_bytes(b'input ')
        self.dst.symlink_to(self.src)
        with self.assertRaises(FileExistsError):
            trim(self.src, self.dst)
        self.assertEqual(self.src.read_bytes(), b'input ')

    def test_long_internal_whitespace_preserved(self):
        spaces = b' ' * 100000
        self.check_conversion(b'a' + spaces + b'b  \n', b'a' + spaces + b'b\n')
