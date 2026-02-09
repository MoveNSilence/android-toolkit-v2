import subprocess
import argparse
import sys
import shutil
import re
import bitstring

def check_adb_installed():
    """Checks if ADB is installed and available in the system path."""
    if shutil.which("adb") is None:
        print("[-] ADB is not installed or not found in PATH.")
        sys.exit(1)

def connect_to_device(device_ip_port):
    """Attempts to connect to the specified Android device via ADB."""
    print(f"[*] Attempting to connect to {device_ip_port}...")
    try:
        # Standard ADB connect command
        result = subprocess.run(
            ["adb", "connect", device_ip_port],
            capture_output=True,
            text=True,
            timeout=10
        )
        if "connected" in result.stdout:
            print("[+] Connection established.")
            return True
        else:
            print(f"[-] Connection failed: {result.stdout.strip()}")
            return False
    except subprocess.TimeoutExpired:
        print("[-] Connection timed out.")
        return False
    except Exception as e:
        print(f"[-] An error occurred: {e}")
        return False

def list_partitions():
    """Lists the partitions on the connected device."""
    print("[*] Pulling partition table for analysis...")
    try:
        subprocess.run(["adb", "shell", "ls -l /dev/block/by-name/"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"[-] Failed to list partitions: {e}")

def luhn_checksum(imei):
    """
    Validates a numeric string using the Luhn algorithm.
    """
    if not imei.isdigit():
        return False
    digits = [int(d) for d in imei]
    # Reverse digits to process from right
    digits.reverse()
    total_sum = 0
    for i, digit in enumerate(digits):
        if i % 2 == 1: # Every second digit (0-indexed so 1, 3, 5...)
            doubled = digit * 2
            if doubled > 9:
                doubled -= 9
            total_sum += doubled
        else:
            total_sum += digit
    return total_sum % 10 == 0

def imei_to_bcd(imei_str):
    """
    Converts a 15-digit IMEI into a 9-byte BCD array for Samsung/Qualcomm.
    Format: [Length][Digit1 + 0xA][Digit3 + Digit2][Digit5 + Digit4]...
    """
    # Standard header for IMEI (length and parity)
    bcd = [0x08]

    # First digit is special (often paired with a 0xA or 0x0 marker)
    first_digit = int(imei_str[0])
    bcd.append((first_digit << 4) | 0x0A)

    # Pair the remaining 14 digits in reverse order (BCD nibble swap)
    for i in range(1, 15, 2):
        d1 = int(imei_str[i])
        d2 = int(imei_str[i+1])
        bcd.append((d2 << 4) | d1)

    return bytes(bcd)

def dump_partitions():
    """Dumps modemst1, modemst2, and fsg partitions to /sdcard/."""
    partitions = ["modemst1", "modemst2", "fsg"]
    for part in partitions:
        print(f"[*] Dumping partition {part}...")
        cmd = f"dd if=/dev/block/by-name/{part} of=/sdcard/{part}.img"
        try:
            # Using su -c to execute dd with root privileges
            subprocess.run(["adb", "shell", "su", "-c", cmd], check=True, capture_output=True, text=True)
            print(f"[+] Dumped {part} to /sdcard/{part}.img")
        except subprocess.CalledProcessError as e:
            print(f"[-] Failed to dump {part}: {e}")

def pull_images():
    """Pulls the dumped .img files from /sdcard/ to the local workspace."""
    images = ["modemst1.img", "modemst2.img", "fsg.img"]
    for img in images:
        print(f"[*] Pulling {img}...")
        try:
            subprocess.run(["adb", "pull", f"/sdcard/{img}", "."], check=True, capture_output=True, text=True)
            print(f"[+] Pulled {img} to current directory")
        except subprocess.CalledProcessError as e:
            print(f"[-] Failed to pull {img}: {e}")

def analyze_image(image_path):
    """Analyzes the binary image for IMEIs and specific hex patterns."""
    print(f"[*] Analyzing {image_path}...")
    findings = []

    # 1. Search for 15-digit ASCII sequences with Luhn check
    try:
        with open(image_path, "rb") as f:
            data = f.read()
            # Regex for 15 digits
            for match in re.finditer(b'\\d{15}', data):
                candidate = match.group().decode('ascii')
                if luhn_checksum(candidate):
                    findings.append(f"Found valid IMEI: {candidate} at offset {match.start()}")
    except Exception as e:
        print(f"[-] Error reading file for text analysis: {e}")
        findings.append(f"Error reading file for text analysis: {e}")

    # 2. Search for Hex patterns using bitstring
    try:
        # bitstring searching
        s = bitstring.ConstBitStream(filename=image_path)

        # 0x088A
        # find returns a generator of bit positions. divide by 8 for byte offset.
        for found in s.find('0x088A', bytealigned=True):
            byte_offset = found // 8
            findings.append(f"Found hex pattern 0x088A at offset {byte_offset} (potential NV Item 550 start)")

        # 0x083A
        for found in s.find('0x083A', bytealigned=True):
            byte_offset = found // 8
            findings.append(f"Found hex pattern 0x083A at offset {byte_offset} (potential NV Item 550 start)")

    except Exception as e:
         print(f"[-] Error during binary analysis: {e}")
         findings.append(f"Error during binary analysis: {e}")

    return findings

def generate_report(findings, output_file="recon_report.txt"):
    """Writes the findings to a report file."""
    try:
        with open(output_file, "a") as f:
            f.write("--- Reconnaissance Report ---\n")
            if not findings:
                f.write("No significant findings.\n")
            for finding in findings:
                f.write(f"{finding}\n")
            f.write("\n")
        print(f"[+] Report appended to {output_file}")
    except Exception as e:
        print(f"[-] Failed to write report: {e}")

def main():
    parser = argparse.ArgumentParser(description="Connect to an Android device via ADB and perform security reconnaissance.")
    parser.add_argument("ip", help="The IP address and port of the Android device (e.g., 192.168.1.11:5555)")
    args = parser.parse_args()

    check_adb_installed()

    if connect_to_device(args.ip):
        list_partitions()

        # Perform Security Reconnaissance
        print("\n[*] Starting Security Reconnaissance...")
        dump_partitions()
        pull_images()

        # Analyze modemst1.img as requested
        # We also have modemst2 and fsg, but requirement specifically mentioned opening modemst1.img for bitstring analysis
        if shutil.which("bitstring") is None and "bitstring" not in sys.modules:
             # Just a check, but we imported it at top
             pass

        img_to_analyze = "modemst1.img"
        try:
            findings = analyze_image(img_to_analyze)
            generate_report(findings)
        except FileNotFoundError:
             print(f"[-] {img_to_analyze} not found. Analysis skipped.")

if __name__ == "__main__":
    main()
