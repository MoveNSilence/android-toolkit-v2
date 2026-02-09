import argparse
import sys
import os

# Ensure the script directory is in the path to allow imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    import device_manager
    import imei_generator
except ImportError:
    # Fallback for running from root
    from src import device_manager
    from src import imei_generator

def main():
    parser = argparse.ArgumentParser(description="Android Toolkit V2: Backup/Wipe Security Partitions and Generate IMEI.")

    parser.add_argument("ip", nargs="?", help="The IP address and port of the Android device (e.g., 192.168.1.11:5555). Required for backup and wipe.")

    parser.add_argument("--backup", action="store_true", help="Analyze and backup EFS/Security partitions.")
    parser.add_argument("--wipe", action="store_true", help="Wipe modemst1 and modemst2 partitions.")
    parser.add_argument("--generate-imei", action="store_true", help="Generate a valid IMEI.")
    parser.add_argument("--tac", help="Optional TAC (Type Allocation Code) for IMEI generation (8 digits).")

    args = parser.parse_args()

    # Handle IMEI generation (doesn't require device connection)
    if args.generate_imei:
        imei = imei_generator.generate_impeccable_imei(tac=args.tac)
        print(f"[+] Generated IMEI: {imei}")
        if not args.backup and not args.wipe:
            sys.exit(0)

    # Check requirements for device operations
    if (args.backup or args.wipe) and not args.ip:
        print("[-] IP address is required for backup or wipe operations.")
        parser.print_help()
        sys.exit(1)

    if args.backup:
        print(f"[*] Starting backup operation on {args.ip}...")
        device_manager.backup_partitions(args.ip)

    if args.wipe:
        print(f"[*] Starting wipe operation on {args.ip}...")
        confirm = input(f"[*] WARNING: You are about to WIPE security partitions on {args.ip}. This is destructive. Type 'YES' to confirm: ")
        if confirm == "YES":
            device_manager.wipe_security_partitions(args.ip)
        else:
            print("[-] Wipe cancelled.")

    if not args.generate_imei and not args.backup and not args.wipe:
        parser.print_help()

if __name__ == "__main__":
    main()
