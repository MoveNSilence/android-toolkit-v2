#!/usr/bin/env python3
import argparse
import sys
import os
import shutil
import time

# Ensure src is in path if running from root
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src import imei
from src import modem
from src import adb_connector
from src import injector

# Try to import InternalBlue, handle if missing (for non-full environments)
try:
    from internalblue.adbcore import ADBCore
    INTERNALBLUE_AVAILABLE = True
except ImportError:
    try:
        from internalblue.hcicore import HCICore as ADBCore # Fallback attempt
        INTERNALBLUE_AVAILABLE = True
    except ImportError:
        INTERNALBLUE_AVAILABLE = False
        print("[-] Warning: InternalBlue not found. 'sync-repair' functionality will be limited.")

class MultiToolBridge:
    """
    Bridge class to handle synchronized ADB sessions between InternalBlue and GodTool_V2 logic.
    Prevents device-lock crashes by managing the sequence of operations.
    """
    def __init__(self, device_ip):
        self.device_ip = device_ip
        self.internalblue = None

    def connect(self):
        """Establishes connection to ADB and InternalBlue."""
        print(f"[*] MultiToolBridge: connecting to {self.device_ip}...")

        # 1. Standard ADB Connection
        if not adb_connector.connect_to_device(self.device_ip):
            print("[-] Failed to establish standard ADB connection.")
            return False

        # 2. InternalBlue Connection
        if INTERNALBLUE_AVAILABLE:
            try:
                # Assuming ADBCore takes serial or device identifier.
                # If using IP over TCP/IP, the serial is the IP:Port string.
                self.internalblue = ADBCore(serial=self.device_ip)
                if not self.internalblue.connect():
                    print("[-] InternalBlue connection failed.")
                    return False
                print("[+] InternalBlue connected.")
            except Exception as e:
                print(f"[-] InternalBlue init failed: {e}")
                return False
        else:
            print("[-] InternalBlue is not available.")
            return False

        return True

    def sync_repair(self, target_image_path, imei_offset_hex, imei_str, bd_addr_str, bd_addr_offset_hex):
        """
        Executes BCD IMEI injection in modemst1 while simultaneously using InternalBlue's writeMem
        to patch the Bluetooth controller's BD_ADDR.
        """
        if not self.connect():
            print("[-] Connection failed. Aborting sync-repair.")
            return False

        print("[*] Starting Sync-Repair Protocol...")

        # Parse inputs
        try:
            bd_addr_offset = int(bd_addr_offset_hex, 16)
            # Parse BD_ADDR string "XX:XX:XX:XX:XX:XX" to bytes
            bd_addr_bytes = bytes.fromhex(bd_addr_str.replace(":", ""))
            if len(bd_addr_bytes) != 6:
                raise ValueError("BD_ADDR must be 6 bytes.")
        except ValueError as e:
            print(f"[-] Invalid input: {e}")
            return False

        # Step 1: Patch Bluetooth BD_ADDR (RAM) via InternalBlue
        print(f"[*] InternalBlue: Patching BD_ADDR at 0x{bd_addr_offset:X}...")
        if self.internalblue:
            if not self.internalblue.writeMem(bd_addr_offset, bd_addr_bytes):
                print("[-] InternalBlue writeMem failed. Aborting.")
                return False
            print("[+] BD_ADDR patched in RAM.")

            # Verify Patch (Parity Check)
            print("[*] Verifying Bluetooth firmware parity...")
            read_back = self.internalblue.readMem(bd_addr_offset, 6)
            if read_back != bd_addr_bytes:
                print(f"[-] Verification failed! Read: {read_back.hex()}, Expected: {bd_addr_bytes.hex()}")
                return False
            print("[+] Bluetooth firmware parity verified.")
        else:
             print("[-] InternalBlue unavailable, skipping BD_ADDR patch (Risk of crash!).")
             # Proceeding? The requirement says "must execute... simultaneously".
             # If unavailable, we can't fulfill the requirement.
             print("[-] Aborting due to missing InternalBlue dependency.")
             return False

        # Step 2: Inject IMEI (Disk)
        print("[*] GodTool: Preparing IMEI injection...")
        if not os.path.exists(target_image_path):
             print(f"[-] Error: Target backup file '{target_image_path}' not found.")
             return False

        try:
             # Create working copy
             filename = os.path.basename(target_image_path)
             base_name, ext = os.path.splitext(filename)
             modified_filename = f"{base_name}_syncrepair{ext}"
             modified_path = os.path.join(os.path.dirname(target_image_path), modified_filename)

             print(f"[*] Creating working copy: {modified_path}...")
             shutil.copyfile(target_image_path, modified_path)

             # Inject
             injector.inject_imei(modified_path, imei_offset_hex, imei_str)

             # Flash
             # Assuming partition name is derived from filename
             partition_name = base_name
             modem.flash_partition(self.device_ip, partition_name, modified_path)

             # Step 3: Validate EFS MD5
             print(f"[*] Validating EFS partition {partition_name}...")
             # Calculate local MD5 of the injected file
             local_md5 = modem.calculate_local_md5(modified_path)

             # Get remote MD5 of the partition (via dd dump or if system supports md5sum on block device)
             # modem.get_remote_md5 takes a file path. We can't run md5sum on /dev/block/... on all devices directly without root/toybox quirks.
             # Ideally we dump it back to /sdcard and check.
             # Reuse verify logic: dump -> check.

             verify_remote_path = f"/sdcard/verify_{partition_name}.img"
             modem.run_adb_command(["shell", "dd", f"if=/dev/block/bootdevice/by-name/{partition_name}", f"of={verify_remote_path}"], self.device_ip)
             remote_md5 = modem.get_remote_md5(verify_remote_path, self.device_ip)
             modem.run_adb_command(["shell", "rm", verify_remote_path], self.device_ip) # Cleanup

             print(f"    Local Injected MD5: {local_md5}")
             print(f"    Remote Partition MD5: {remote_md5}")

             if local_md5 != remote_md5:
                 print("[-] FATAL: EFS MD5 Mismatch! Flash verification failed.")
                 return False
             print("[+] EFS MD5 verified.")

        except Exception as e:
             print(f"[-] Sync-Repair operation failed: {e}")
             return False

        # Step 4: Final Reboot
        print("[*] Operation successful. Rebooting device...")
        modem.run_adb_command(["reboot"], self.device_ip)
        print("[+] Device rebooting. Sync-Repair complete.")
        return True


def main():
    parser = argparse.ArgumentParser(description="God Tool (Samsung/Motorola) - Device Security Analysis & Modification")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Common argument: IP
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

    # Sync-Repair
    parser_sync = subparsers.add_parser("sync-repair", help="Execute synchronized IMEI injection and Bluetooth patch")
    parser_sync.add_argument("--target", help="Target partition image file (e.g., backups/modemst1.img)", required=True)
    parser_sync.add_argument("--offset", help="IMEI Hex offset address", required=True)
    parser_sync.add_argument("--imei", help="New IMEI", required=True)
    parser_sync.add_argument("--bd-addr", help="New Bluetooth Address (XX:XX:XX:XX:XX:XX)", required=True)
    parser_sync.add_argument("--bd-addr-offset", help="Bluetooth Address Hex Offset in RAM", required=True)

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
        # We generally expect connection to be possible
        # But MultiToolBridge handles its own connection for sync-repair

    if args.command == "connect":
        require_ip()
        if adb_connector.connect_to_device(args.ip):
            adb_connector.list_partitions()

    elif args.command == "generate-imei":
        try:
            generated = imei.generate_imei(args.tac)
            print(f"[+] Generated IMEI: {generated}")
        except ValueError as e:
            print(f"[-] Error: {e}")

    elif args.command == "enable-diag":
        require_ip()
        if adb_connector.connect_to_device(args.ip):
            modem.enable_diag_mode(args.ip)

    elif args.command == "backup":
        require_ip()
        if adb_connector.connect_to_device(args.ip):
            try:
                modem.backup_efs(args.ip, args.dir)
            except Exception as e:
                print(f"[-] Backup Failed: {e}")

    elif args.command == "wipe":
        require_ip()
        if adb_connector.connect_to_device(args.ip):
            try:
                modem.wipe_efs(args.ip, args.dir)
            except Exception as e:
                print(f"[-] Wipe Failed: {e}")

    elif args.command == "inject":
        require_ip()
        if adb_connector.connect_to_device(args.ip):
            target_path = args.target
            offset = args.offset
            new_imei = args.imei

            if not os.path.exists(target_path):
                 print(f"[-] Error: Target backup file '{target_path}' not found. Please perform a backup first.")
                 sys.exit(1)

            try:
                 filename = os.path.basename(target_path)
                 base_name, ext = os.path.splitext(filename)
                 modified_filename = f"{base_name}_injected{ext}"
                 modified_path = os.path.join(os.path.dirname(target_path), modified_filename)

                 print(f"[*] Creating working copy: {modified_path}...")
                 shutil.copyfile(target_path, modified_path)

                 injector.inject_imei(modified_path, offset, new_imei)

                 partition_name = base_name
                 modem.flash_partition(args.ip, partition_name, modified_path)

                 print(f"[+] Process complete. Injected image: {modified_path}")

            except Exception as e:
                 print(f"[-] Injection/Flash Failed: {e}")

    elif args.command == "sync-repair":
        # Check IP but don't force connect via adb_connector first, let Bridge handle it
        if not args.ip:
            print("[-] Error: Device IP is required for this command. Use --ip <IP>.")
            sys.exit(1)

        bridge = MultiToolBridge(args.ip)
        bridge.sync_repair(args.target, args.offset, args.imei, args.bd_addr, args.bd_addr_offset)

if __name__ == "__main__":
    main()
