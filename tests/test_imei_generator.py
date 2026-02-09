import unittest
import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from imei_generator import generate_impeccable_imei, calculate_luhn_checksum

class TestIMEIGenerator(unittest.TestCase):

    def test_length(self):
        imei = generate_impeccable_imei()
        self.assertEqual(len(imei), 15)
        self.assertTrue(imei.isdigit())

    def test_with_tac(self):
        tac = "12345678"
        imei = generate_impeccable_imei(tac=tac)
        self.assertTrue(imei.startswith(tac))
        self.assertEqual(len(imei), 15)

    def test_checksum(self):
        # Known valid IMEI prefixes (14 digits)
        # 35293206236318 -> Check digit 7
        payload = "35293206236318"
        check_digit = calculate_luhn_checksum(payload)
        self.assertEqual(check_digit, 7)

        # 86254002626630 -> Check digit 6
        payload = "86254002626630"
        check_digit = calculate_luhn_checksum(payload)
        self.assertEqual(check_digit, 6)

    def test_generated_imei_validity(self):
        # Generate an IMEI and verify its check digit matches our calculation
        imei = generate_impeccable_imei()
        payload = imei[:14]
        check_digit = int(imei[14])
        self.assertEqual(calculate_luhn_checksum(payload), check_digit)

if __name__ == '__main__':
    unittest.main()
