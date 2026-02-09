import random

def calculate_luhn_checksum(imei_14):
    """Calculates the Luhn checksum digit for the first 14 digits."""
    digits = [int(d) for d in imei_14]
    sum_val = 0

    # For a 15-digit IMEI, the check digit is at index 14.
    # Verification doubles every second digit from the right.
    # Starting from the check digit (index 14), the "second digit" is at index 13.
    # So indices 13, 11, 9, 7, 5, 3, 1 are doubled.
    # These are the ODD indices (0-based).

    for i, digit in enumerate(digits):
        if i % 2 != 0: # Odd index: 1, 3, ... 13
            doubled = digit * 2
            if doubled > 9:
                sum_val += (doubled - 9)
            else:
                sum_val += doubled
        else: # Even index: 0, 2, ... 12
            sum_val += digit

    return (10 - (sum_val % 10)) % 10

def generate_impeccable_imei(tac=None):
    """
    Generates a valid 15-digit IMEI using the Luhn checksum.

    Args:
        tac (str, optional): The 8-digit Type Allocation Code.
                             If None, a random one is generated.

    Returns:
        str: A valid 15-digit IMEI.
    """
    if tac is None:
        # Generate random 8-digit TAC
        tac = "".join([str(random.randint(0, 9)) for _ in range(8)])
    else:
        tac = str(tac)
        # Ensure only digits
        tac = "".join(filter(str.isdigit, tac))
        if len(tac) != 8:
             # Just a basic check, we'll try to use it or pad/truncate
             pass

    # Generate 6-digit SNR
    snr = "".join([str(random.randint(0, 9)) for _ in range(6)])

    imei_14 = tac + snr

    # Ensure we only have 14 digits
    imei_14 = imei_14[:14]

    # Fill if short
    while len(imei_14) < 14:
        imei_14 += str(random.randint(0, 9))

    check_digit = calculate_luhn_checksum(imei_14)

    return imei_14 + str(check_digit)

if __name__ == "__main__":
    print(generate_impeccable_imei())
