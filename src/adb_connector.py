import subprocess
import argparse
import sys
import shutil

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

def main():
    parser = argparse.ArgumentParser(description="Connect to an Android device via ADB and list partitions.")
    parser.add_argument("ip", help="The IP address and port of the Android device (e.g., 192.168.1.11:5555)")
    args = parser.parse_args()

    if not check_adb_installed():
        sys.exit(1)

    if connect_to_device(args.ip):
        list_partitions()

if __name__ == "__main__":
    main()
