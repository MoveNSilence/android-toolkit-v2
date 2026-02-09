import unittest
import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

import adb_connector

class TestImeiUtils(unittest.TestCase):
    def test_imei_to_bcd(self):
        imei = "123456789012345"
        # BCD should be:
        # [0x08]
        # [0x1A] -> 1st digit '1' << 4 | 0x0A
        # Pair 2,3: '2','3' -> (3<<4)|2 = 0x32
        # Pair 4,5: '4','5' -> (5<<4)|4 = 0x54
        # Pair 6,7: '6','7' -> (7<<4)|6 = 0x76
        # Pair 8,9: '8','9' -> (9<<4)|8 = 0x98
        # Pair 0,1: '0','1' -> (1<<4)|0 = 0x10
        # Pair 2,3: '2','3' -> (3<<4)|2 = 0x32
        # Pair 4,5: '4','5' -> (5<<4)|4 = 0x54

        expected = bytes([0x08, 0x1A, 0x32, 0x54, 0x76, 0x98, 0x10, 0x32, 0x54])
        result = adb_connector.imei_to_bcd(imei)

        self.assertEqual(result, expected)

if __name__ == '__main__':
    unittest.main()
