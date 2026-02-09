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

if __name__ == "__main__":
    print(f"Generated IMEI: {generate_imei()}")
