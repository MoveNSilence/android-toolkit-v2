import subprocess
import time

def check_adb_installed():
    """
    Checks if ADB is installed and accessible.
    """
    try:
        subprocess.run(["adb", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False

def connect_to_device(device_ip_port):
    """
    Connects to an Android device over ADB using the provided IP and port.
    """
    print(f"[*] Attempting to hijack connection to {device_ip_port}...")

    if not check_adb_installed():
        print("[-] ADB executable not found. Please ensure Android Platform Tools are installed and in your PATH.")
        return False

    # Standard ADB connect command
    try:
        result = subprocess.run(["adb", "connect", device_ip_port], capture_output=True, text=True)
        # ADB output for successful connection usually contains "connected to <ip>"
        # If already connected, it says "already connected to <ip>"
        if "connected" in result.stdout.lower():
            print("[+] Connection established. Device is in the loop.")
            return True
        else:
            print(f"[-] Connection attempt failed. Output: {result.stdout.strip()}")
            return False
    except Exception as e:
        print(f"[-] An unexpected error occurred: {e}")
        return False
