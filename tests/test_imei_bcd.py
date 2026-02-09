import unittest
from src.imei import imei_to_bcd

class TestIMEIBCD(unittest.TestCase):
    def test_imei_to_bcd_valid(self):
        # Example IMEI: 358270000000007
        # Digits: 3, 5, 8, 2, 7, 0, 0, 0, 0, 0, 0, 0, 0, 0, 7
        # Header: 0x08
        # Digit 1: 3. Byte: (3 << 4) | 0xA = 0x3A.
        # Digits 2, 3: 5, 8. Byte: (8 << 4) | 5 = 0x85.
        # Digits 4, 5: 2, 7. Byte: (7 << 4) | 2 = 0x72.
        # Digits 6, 7: 0, 0. Byte: 0x00.
        # Digits 8, 9: 0, 0. Byte: 0x00.
        # Digits 10, 11: 0, 0. Byte: 0x00.
        # Digits 12, 13: 0, 0. Byte: 0x00.
        # Digits 14, 15: 0, 7. Byte: (7 << 4) | 0 = 0x70.

        imei = "358270000000007"
        expected_bcd = bytes([0x08, 0x3A, 0x85, 0x72, 0x00, 0x00, 0x00, 0x00, 0x70])

        result = imei_to_bcd(imei)
        self.assertEqual(result, expected_bcd)

    def test_imei_to_bcd_invalid_length(self):
        with self.assertRaises(ValueError):
            imei_to_bcd("12345")

    def test_imei_to_bcd_non_numeric(self):
        with self.assertRaises(ValueError):
            imei_to_bcd("35827000000000A")

if __name__ == "__main__":
    unittest.main()
