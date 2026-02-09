import random

def calculate_luhn_check_digit(digits):
    """
    Calculates the Luhn check digit for a list of 14 digits (IMEI payload).
    """
    if len(digits) != 14:
        raise ValueError("Input must be a list of 14 digits.")

    sum_ = 0
    # For 15-digit IMEI, the pattern from left (index 0) is:
    # Index 0: No double
    # Index 1: Double
    # ...
    # Index 13: Double
    # Index 14: Check Digit (No double)

    for i, digit in enumerate(digits):
        if i % 2 == 1: # Odd index (1, 3, ... 13) -> Double
            doubled = 2 * digit
            if doubled > 9:
                doubled -= 9
            sum_ += doubled
        else: # Even index (0, 2, ... 12) -> No double
            sum_ += digit

    return (10 - (sum_ % 10)) % 10

def generate_imei(tac="358270"):
    """
    Generates a valid 15-digit IMEI using the provided TAC.
    Defaults to Samsung TAC (358270).
    """
    if not tac:
        tac = "358270"

    # Clean TAC
    tac = str(tac).strip()
    if not tac.isdigit():
        raise ValueError("TAC must be numeric.")

    digits = [int(d) for d in tac]

    # We need 14 digits total before check digit.
    needed = 14 - len(digits)

    if needed < 0:
         raise ValueError(f"TAC is too long ({len(digits)}). Must be 14 digits or less.")

    for _ in range(needed):
        digits.append(random.randint(0, 9))

    check_digit = calculate_luhn_check_digit(digits)
    digits.append(check_digit)

    return "".join(map(str, digits))


def imei_to_bcd(imei_str):
    """
    Converts a 15-digit IMEI into a 9-byte BCD array for Samsung/Qualcomm.
    Format: [Length][Digit1 + 0xA][Digit3 + Digit2][Digit5 + Digit4]...
    """
    if len(imei_str) != 15 or not imei_str.isdigit():
        raise ValueError("IMEI must be a 15-digit numeric string.")

    # Standard header for IMEI (length and parity)
    bcd = [0x08]

    # First digit is special (often paired with a 0xA marker)
    first_digit = int(imei_str[0])
    bcd.append((first_digit << 4) | 0x0A)

    # Pair the remaining 14 digits in reverse order (BCD nibble swap)
    for i in range(1, 15, 2):
        d1 = int(imei_str[i])
        d2 = int(imei_str[i+1])
        bcd.append((d2 << 4) | d1)

    return bytes(bcd)


if __name__ == "__main__":
    print(f"Generated IMEI: {generate_imei()}")
