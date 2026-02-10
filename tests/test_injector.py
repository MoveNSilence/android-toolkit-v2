import unittest
import os
from src.injector import inject_imei
from src.imei import imei_to_bcd

class TestInjector(unittest.TestCase):
    def setUp(self):
        # Create a dummy file
        self.filename = "test_image.bin"
        self.file_size = 1024
        with open(self.filename, "wb") as f:
            f.write(b"\x00" * self.file_size)

    def tearDown(self):
        if os.path.exists(self.filename):
            os.remove(self.filename)

    def test_inject_imei_valid(self):
        imei = "358270000000007"
        offset_hex = "0x100"
        offset_int = 256

        inject_imei(self.filename, offset_hex, imei)

        # Verify content
        with open(self.filename, "rb") as f:
            f.seek(offset_int)
            read_data = f.read(9)
            expected_data = imei_to_bcd(imei)
            self.assertEqual(read_data, expected_data)

    def test_inject_imei_invalid_offset(self):
        imei = "358270000000007"
        with self.assertRaises(ValueError):
            inject_imei(self.filename, "invalid_hex", imei)

    def test_inject_imei_invalid_imei(self):
        with self.assertRaises(ValueError):
            inject_imei(self.filename, "0x100", "123")

    def test_inject_imei_file_not_found(self):
        imei = "358270000000007"
        with self.assertRaises(FileNotFoundError):
            inject_imei("nonexistent.bin", "0x100", imei)

if __name__ == "__main__":
    unittest.main()
