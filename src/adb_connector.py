import subprocess
import argparse
import sys
import shutil
import bitstring
import re
import os
try:
    from src.imei import imei_to_bcd
except ImportError:
    # Fallback for when running directly or tests
    try:
        from imei import imei_to_bcd
    except ImportError:
         print("[-] Could not import imei_to_bcd")

def check_adb_installed():
    """Checks if ADB is installed and available in the system path."""
    if shutil.which("adb") is None:
        print("[-] ADB is not installed or not found in PATH.")
        return False
    return True

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

def luhn_checksum(n_str):
    """Checks if a string of digits satisfies the Luhn algorithm."""
    try:
        r = [int(ch) for ch in n_str][::-1]
        return (sum(r[0::2]) + sum(sum(divmod(d*2,10)) for d in r[1::2])) % 10 == 0
    except ValueError:
        return False

def inject_imei_to_image(image_path, offset, new_imei):
    """
    Overwrites the IMEI at a specific hex offset in the partition image.
    :param image_path: Path to the .img or .bin file (e.g., modemst1.img)
    :param offset: The hex offset found during the Recon phase (e.g., 0x000A1BC)
    :param new_imei: The 15-digit impeccable IMEI string
    """
    if len(new_imei) != 15 or not new_imei.isdigit():
        print("[-] Invalid IMEI format. Must be 15 digits.")
        return False

    if not luhn_checksum(new_imei):
        print("[-] Invalid IMEI. Luhn check failed.")
        return False

    try:
        imei_bytes = imei_to_bcd(new_imei)
    except Exception as e:
        print(f"[-] Failed to convert IMEI to BCD: {e}")
        return False

    print(f"[*] Injecting identity into {image_path} at offset {hex(offset)}...")

    try:
        with open(image_path, 'r+b') as f:
            f.seek(offset)
            f.write(imei_bytes)
        print("[+] Injection successful. Verification required via MD5.")
        return True
    except FileNotFoundError:
        print(f"[-] File {image_path} not found.")
        return False
    except Exception as e:
        print(f"[-] Injection failed: {e}")
        return False

class SecurityRecon:
    def __init__(self, device_ip):
        self.device_ip = device_ip

    def dump_partitions(self):
        """Dumps modemst1, modemst2, and fsg partitions."""
        partitions = ['modemst1', 'modemst2', 'fsg']
        print("[*] Dumping partitions...")
        for part in partitions:
            # Using 'dd' to dump partition to sdcard
            cmd = f"adb shell su -c 'dd if=/dev/block/by-name/{part} of=/sdcard/{part}.img'"
            print(f"[*] Executing: {cmd}")
            try:
                subprocess.run(cmd, shell=True, check=True)
            except subprocess.CalledProcessError as e:
                print(f"[-] Failed to dump {part}: {e}")
                return False
        return True

    def pull_images(self):
        """Pulls partition images to local workspace."""
        partitions = ['modemst1', 'modemst2', 'fsg']
        print("[*] Pulling images...")
        for part in partitions:
            cmd = ["adb", "pull", f"/sdcard/{part}.img", "."]
            print(f"[*] Executing: {' '.join(cmd)}")
            try:
                subprocess.run(cmd, check=True)
            except subprocess.CalledProcessError as e:
                print(f"[-] Failed to pull {part}.img: {e}")
                return False
        return True

    def check_luhn(self, n_str):
        """Checks if a string of digits satisfies the Luhn algorithm."""
        return luhn_checksum(n_str)

    def scan_img(self, filename):
        """Scans the image for IMEIs and specific hex patterns."""
        print(f"[*] Scanning {filename}...")
        results = {'imeis': [], 'patterns': []}

        if not os.path.exists(filename):
            print(f"[-] File {filename} not found.")
            return results

        try:
            # Open with bitstring for pattern search
            # Using ConstBitStream for read-only access
            s = bitstring.ConstBitStream(filename=filename)

            # Search for hex patterns
            # 08 8A and 08 3A are specified in the requirements
            patterns = [('0x088A', 'NV Item 550 Marker (8...)'), ('0x083A', 'NV Item 550 Marker (3...)')]

            for pattern, desc in patterns:
                # findall returns generator of bit positions
                # bytealigned=True ensures we search on byte boundaries
                found = list(s.findall(pattern, bytealigned=True))
                for bit_pos in found:
                    byte_offset = bit_pos // 8
                    results['patterns'].append({
                        'pattern': pattern,
                        'description': desc,
                        'offset': byte_offset
                    })
                    print(f"[+] Found pattern {pattern} at offset {byte_offset}")

            # Search for 15-digit numeric sequences
            # We convert the bitstream to bytes to use regex, which is efficient for this pattern
            s.bytepos = 0
            file_bytes = s.bytes

            # Regex for 15 digits
            digit_pattern = re.compile(b'\\d{15}')

            for match in digit_pattern.finditer(file_bytes):
                candidate = match.group().decode('ascii')
                offset = match.start()
                if self.check_luhn(candidate):
                    results['imeis'].append({
                        'value': candidate,
                        'offset': offset
                    })
                    print(f"[+] Found valid IMEI candidate: {candidate} at offset {offset}")

        except Exception as e:
            print(f"[-] Error scanning {filename}: {e}")

        return results

    def run(self):
        """Orchestrates the recon mission."""

        if not self.dump_partitions():
            print("[-] Partition dump failed. Aborting.")
            return

        if not self.pull_images():
            print("[-] Image pull failed. Aborting.")
            return

        # Only scan modemst1.img as per instructions
        scan_results = self.scan_img("modemst1.img")

        # Generate report
        report_filename = "recon_report.txt"
        try:
            with open(report_filename, "w") as f:
                f.write("Security Reconnaissance Report\n")
                f.write("==============================\n\n")

                f.write("Found Patterns:\n")
                if not scan_results['patterns']:
                    f.write("None found.\n")
                else:
                    for p in scan_results['patterns']:
                        f.write(f"Pattern: {p['pattern']} ({p['description']}) at Offset: {p['offset']}\n")

                f.write("\nFound IMEI Candidates:\n")
                if not scan_results['imeis']:
                    f.write("None found.\n")
                else:
                    for i in scan_results['imeis']:
                        f.write(f"IMEI: {i['value']} at Offset: {i['offset']}\n")
            print(f"[+] Report generated: {report_filename}")
        except IOError as e:
            print(f"[-] Failed to write report: {e}")

def main():
    parser = argparse.ArgumentParser(description="Connect to an Android device via ADB and list partitions.")
    parser.add_argument("ip", help="The IP address and port of the Android device (e.g., 192.168.1.11:5555)", nargs='?')
    parser.add_argument("--recon", action="store_true", help="Perform Security Reconnaissance mission")
    parser.add_argument("--inject", help="IMEI to inject")
    parser.add_argument("--offset", help="Hex offset for injection")
    parser.add_argument("--image", default="modemst1.img", help="Image file to inject into (default: modemst1.img)")
    args = parser.parse_args()

    if args.inject:
        if not args.offset:
            print("[-] --offset is required for injection.")
            sys.exit(1)
        try:
            offset = int(args.offset, 16)
        except ValueError:
            print("[-] Invalid offset format. Must be hex (e.g., 0x1234).")
            sys.exit(1)

        inject_imei_to_image(args.image, offset, args.inject)
        return

    if not args.ip:
        parser.print_help()
        sys.exit(1)

    if not check_adb_installed():
        sys.exit(1)

    if connect_to_device(args.ip):
        if args.recon:
            recon = SecurityRecon(args.ip)
            recon.run()
        else:
            list_partitions()

if __name__ == "__main__":
    main()
