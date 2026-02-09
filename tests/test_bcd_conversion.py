import pytest
import sys
import os

# Ensure src is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.imei import imei_to_bcd

def test_imei_to_bcd_valid():
    # Example IMEI: 358270031234567
    # BCD format:
    # 0x08 (Length)
    # First digit 3: (3 << 4) | 0xA = 0x3A
    # Remaining 14 digits: 58 27 00 31 23 45 67
    # Nibble swapped:
    # 58 -> 0x85
    # 27 -> 0x72
    # 00 -> 0x00
    # 31 -> 0x13
    # 23 -> 0x32
    # 45 -> 0x54
    # 67 -> 0x76

    imei = "358270031234567"
    expected = bytes([
        0x08,
        0x3A,
        0x85, 0x72, 0x00, 0x13, 0x32, 0x54, 0x76
    ])

    assert imei_to_bcd(imei) == expected

def test_imei_to_bcd_invalid_length():
    with pytest.raises(ValueError):
        imei_to_bcd("12345678901234") # 14 digits

def test_imei_to_bcd_non_numeric():
    with pytest.raises(ValueError):
        imei_to_bcd("35827003123456a")
