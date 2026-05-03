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
    parser.add_argument("--target", help="Target device IP:PORT")

    args = parser.parse_args()

    # Priority: 1. Command-line argument, 2. Environment variable
    target = args.target or os.environ.get("GOD_TOOL_TARGET")

    if not target:
        print("[X] Error: No target device specified.")
        print("    Use --target <IP:PORT> or set the GOD_TOOL_TARGET environment variable.")
        sys.exit(1)

    if connect_to_device(target):
        analyze_partitions()
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
