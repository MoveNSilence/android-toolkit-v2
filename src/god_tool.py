#!/usr/bin/env python3
import argparse
import sys
import os
import shutil

# Ensure src is in path if running from root
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src import imei
from src import modem
from src import adb_connector
from src import injector

def main():
    parser = argparse.ArgumentParser(description="God Tool (Samsung/Motorola) - Device Security Analysis & Modification")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Common argument: IP
    # We add it to each parser or as a global argument? Global is cleaner.
    parser.add_argument("--ip", help="Device IP address (e.g., 192.168.1.15:5555)")

    # Connect
    parser_connect = subparsers.add_parser("connect", help="Test connection to device")

    # Generate IMEI
    parser_imei = subparsers.add_parser("generate-imei", help="Generate valid IMEI")
    parser_imei.add_argument("--tac", help="Type Allocation Code (TAC). Default: Samsung (358270)", default="358270")

    # Enable Diag
    parser_diag = subparsers.add_parser("enable-diag", help="Enable Diag Mode (diag,adb)")

    # Backup EFS
    parser_backup = subparsers.add_parser("backup", help="Backup EFS partitions (modemst1, modemst2, fsg)")
    parser_backup.add_argument("--dir", help="Backup directory", default="backups")

    # Wipe EFS
    parser_wipe = subparsers.add_parser("wipe", help="Wipe EFS partitions (Requires Backup)")
    parser_wipe.add_argument("--dir", help="Backup directory to verify against", default="backups")

    # Inject IMEI
    parser_inject = subparsers.add_parser("inject", help="Inject IMEI into partition image and flash")
    parser_inject.add_argument("--target", help="Target partition image file (e.g., backups/modemst1.img)", required=True)
    parser_inject.add_argument("--offset", help="Hex offset address (e.g., 0x1234)", required=True)
    parser_inject.add_argument("--imei", help="New IMEI to inject", required=True)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Helper to check IP requirement
    def require_ip():
        if not args.ip:
            print("[-] Error: Device IP is required for this command. Use --ip <IP>.")
            sys.exit(1)
        if not adb_connector.check_adb_installed():
            sys.exit(1)
        # Attempt connection or check if already connected?
        # adb_connector.connect_to_device(args.ip)
        # We can just assume adb connects on demand or user ran connect first.
        # But good practice to ensure connection.
        if not adb_connector.connect_to_device(args.ip):
            print("[-] failed to connect to device.")
            sys.exit(1)

    if args.command == "connect":
        require_ip()
        adb_connector.list_partitions()

    elif args.command == "generate-imei":
        try:
            generated = imei.generate_imei(args.tac)
            print(f"[+] Generated IMEI: {generated}")
            # Verify validity just to be sure
            # (Already done in generation logic)
        except ValueError as e:
            print(f"[-] Error: {e}")

    elif args.command == "enable-diag":
        require_ip()
        modem.enable_diag_mode(args.ip)

    elif args.command == "backup":
        require_ip()
        try:
            modem.backup_efs(args.ip, args.dir)
        except Exception as e:
            print(f"[-] Backup Failed: {e}")

    elif args.command == "wipe":
        require_ip()
        try:
            modem.wipe_efs(args.ip, args.dir)
        except Exception as e:
            print(f"[-] Wipe Failed: {e}")

    elif args.command == "inject":
        require_ip()

        target_path = args.target
        offset = args.offset
        new_imei = args.imei

        # Check if backup exists (Safety Check)
        if not os.path.exists(target_path):
             print(f"[-] Error: Target backup file '{target_path}' not found. Please perform a backup first.")
             sys.exit(1)

        try:
             # Create a copy to work on, preserving the original backup
             filename = os.path.basename(target_path)
             base_name, ext = os.path.splitext(filename)
             modified_filename = f"{base_name}_injected{ext}"
             modified_path = os.path.join(os.path.dirname(target_path), modified_filename)

             print(f"[*] Creating working copy: {modified_path}...")
             shutil.copyfile(target_path, modified_path)

             # 1. Inject into the copy
             injector.inject_imei(modified_path, offset, new_imei)

             # 2. Flash
             # Determine partition name from filename
             # User provides --target backups/modemst1.img -> modemst1
             partition_name = base_name

             # Basic validation of partition name
             # The partition name on device usually matches the filename without extension if adhering to convention
             # But let's just use the base name.

             modem.flash_partition(args.ip, partition_name, modified_path)

             print(f"[+] Process complete. Injected image: {modified_path}")

        except Exception as e:
             print(f"[-] Injection/Flash Failed: {e}")
             # Optional cleanup of modified file on failure?
             # if os.path.exists(modified_path):
             #    os.remove(modified_path)

if __name__ == "__main__":
    main()
