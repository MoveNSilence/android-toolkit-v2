import argparse
import subprocess
import sys
import os

# Allow running from src directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from src.adb_connector import connect_to_device
except ImportError:
    # If run as a script from root, this might be needed or if installed as package
    from adb_connector import connect_to_device

# Default target IP from snippet
DEFAULT_TARGET_IP = "10.0.0.193:43261"

def analyze_partitions():
    """
    Analyzes the partition table by listing /dev/block/by-name/
    """
    print("[*] Pulling partition table for analysis...")
    try:
        subprocess.run(["adb", "shell", "ls -l /dev/block/by-name/"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"[-] Command failed: {e}")

def main():
    parser = argparse.ArgumentParser(description="GodTool V2 - Android Repair & Analysis Tool")
    parser.add_argument("--target", default=DEFAULT_TARGET_IP, help="Target device IP:PORT")

    args = parser.parse_args()

    if connect_to_device(args.target):
        analyze_partitions()
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
