import unittest
import os
import sys

# Ensure src is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.adb_connector import inject_imei_to_image, luhn_checksum
from src.imei import imei_to_bcd

class TestInjection(unittest.TestCase):
    def setUp(self):
        self.test_file = "test_image.img"
        self.valid_imei = "358456070188000"
        # Create a dummy file with 100 bytes of zeros
        with open(self.test_file, "wb") as f:
            f.write(b'\x00' * 100)

    def tearDown(self):
        if os.path.exists(self.test_file):
            os.remove(self.test_file)

    def test_luhn_checksum(self):
        self.assertTrue(luhn_checksum(self.valid_imei))
        self.assertFalse(luhn_checksum("358456070188019"))

    def test_injection(self):
        offset = 0x10

        result = inject_imei_to_image(self.test_file, offset, self.valid_imei)
        self.assertTrue(result)

        with open(self.test_file, "rb") as f:
            f.seek(offset)
            content = f.read(9)
            expected = imei_to_bcd(self.valid_imei)
            self.assertEqual(content, expected)

    def test_invalid_imei_length(self):
        offset = 0x10
        invalid_imei = "123"
        result = inject_imei_to_image(self.test_file, offset, invalid_imei)
        self.assertFalse(result)

    def test_invalid_imei_luhn(self):
        offset = 0x10
        invalid_imei = "358456070188019" # Invalid Luhn
        result = inject_imei_to_image(self.test_file, offset, invalid_imei)
        self.assertFalse(result)

    def test_file_not_found(self):
        offset = 0x10
        result = inject_imei_to_image("non_existent.img", offset, self.valid_imei)
        self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()
