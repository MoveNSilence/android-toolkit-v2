import unittest
from src.imei import calculate_luhn_check_digit, generate_imei

class TestIMEI(unittest.TestCase):
    def test_luhn_check_digit(self):
        # Known valid IMEI prefixes (14 digits) and their check digits
        # Example from online generator
        # 35827000000000 -> Check digit should be calculated
        # Let's verify manually.
        # 3 5 8 2 7 0 0 0 0 0 0 0 0 0
        # d0 d1 ...
        # Double odd indices: 5->10(1), 2->4, 0->0...
        # Sum:
        # d0(3) + d1(1) + d2(8) + d3(4) + d4(7) + ...
        # 3 + 1 + 8 + 4 + 7 = 23.
        # Check digit: (10 - 3) % 10 = 7.
        # So 358270000000007 should be valid.

        digits = [3, 5, 8, 2, 7, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        check = calculate_luhn_check_digit(digits)
        self.assertEqual(check, 7)

    def test_generate_imei_length(self):
        imei = generate_imei()
        self.assertEqual(len(imei), 15)
        self.assertTrue(imei.isdigit())

    def test_generate_imei_luhn_validity(self):
        imei = generate_imei()
        digits = [int(d) for d in imei]
        # Verify manually
        sum_ = 0
        for i, digit in enumerate(digits):
            if i % 2 == 1: # Odd index - Double
                 doubled = 2 * digit
                 if doubled > 9:
                     doubled -= 9
                 sum_ += doubled
            else:
                 sum_ += digit

        self.assertEqual(sum_ % 10, 0, f"IMEI {imei} is invalid")

    def test_generate_imei_custom_tac(self):
        tac = "12345678"
        imei = generate_imei(tac)
        self.assertTrue(imei.startswith(tac))
        self.assertEqual(len(imei), 15)

        # Verify validity
        digits = [int(d) for d in imei]
        sum_ = 0
        for i, digit in enumerate(digits):
            if i % 2 == 1:
                 doubled = 2 * digit
                 if doubled > 9:
                     doubled -= 9
                 sum_ += doubled
            else:
                 sum_ += digit
        self.assertEqual(sum_ % 10, 0)

if __name__ == "__main__":
    unittest.main()
