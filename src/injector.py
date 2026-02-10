import os
import sys
from src import imei

def inject_imei(image_path, offset_hex, imei_str):
    """
    Injects the given IMEI into the specified image file at the given offset.
    """
    print(f"[*] Starting IMEI Injection for {image_path}...")

    # 1. Validate IMEI
    if len(imei_str) != 15 or not imei_str.isdigit():
        raise ValueError("IMEI must be a 15-digit numeric string.")

    # 2. Convert Offset
    try:
        offset = int(offset_hex, 16)
    except ValueError:
        raise ValueError(f"Invalid hex offset: {offset_hex}")

    # 3. Convert IMEI to BCD
    try:
        bcd_data = imei.imei_to_bcd(imei_str)
    except Exception as e:
        raise ValueError(f"Failed to convert IMEI to BCD: {e}")

    # 4. Write to File
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image file not found: {image_path}")

    try:
        with open(image_path, "r+b") as f:
            f.seek(offset)
            f.write(bcd_data)
        print(f"[+] Successfully injected IMEI {imei_str} at offset {offset_hex} (0x{offset:X}).")
    except Exception as e:
        raise IOError(f"Failed to write to file: {e}")
