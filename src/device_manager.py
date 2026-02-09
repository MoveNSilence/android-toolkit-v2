import os
import sys

# Ensure we can import adb_connector from the same directory
try:
    import adb_connector
except ImportError:
    # If running from root as a module or script
    from src import adb_connector

def find_security_partitions():
    """
    Lists partitions and filters for security-related ones.
    Specifically looks for 'modemst1', 'modemst2', and any partition containing 'efs'.
    """
    output = adb_connector.list_partitions()
    if not output:
        print("[-] Failed to list partitions.")
        return []

    partitions = []
    lines = output.split('\n')
    for line in lines:
        parts = line.split()
        # Typical output: lrwxrwxrwx ... partition_name -> /dev/block/mmcblk0pX
        if '->' in parts:
            try:
                arrow_index = parts.index('->')
                if arrow_index > 0:
                    partition_name = parts[arrow_index - 1]
                    # Check if it's relevant
                    if partition_name in ['modemst1', 'modemst2'] or 'efs' in partition_name:
                        partitions.append(partition_name)
            except ValueError:
                continue

    # Remove duplicates if any
    return list(set(partitions))

def backup_partitions(device_ip):
    """
    Backs up security partitions from the device.
    """
    if not adb_connector.connect_to_device(device_ip):
        return

    print("[*] Analyzing partitions...")
    partitions = find_security_partitions()

    if not partitions:
        print("[-] No security partitions found.")
        return

    print(f"[*] Found partitions: {', '.join(partitions)}")

    backup_dir = "backups"
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)

    for part in partitions:
        print(f"[*] Backing up {part}...")
        remote_path = f"/sdcard/{part}.img"
        # dd command
        cmd = f"dd if=/dev/block/by-name/{part} of={remote_path}"

        # Execute dd
        result = adb_connector.execute_shell_command(cmd)
        if result is None:
            print(f"[-] Failed to execute dd for {part}")
            continue

        local_path = os.path.join(backup_dir, f"{part}.img")
        if adb_connector.pull_file(remote_path, local_path):
            print(f"[+] Backup of {part} saved to {local_path}")
            # Clean up
            adb_connector.execute_shell_command(f"rm {remote_path}")
        else:
            print(f"[-] Failed to backup {part}")

def wipe_security_partitions(device_ip):
    """
    Wipes modemst1 and modemst2 partitions.
    """
    if not adb_connector.connect_to_device(device_ip):
        return

    targets = ['modemst1', 'modemst2']

    print("[*] Verifying partition existence...")
    found_partitions = find_security_partitions()

    for target in targets:
        if target in found_partitions:
            print(f"[*] Wiping {target}...")
            # WARNING: destructive operation
            cmd = f"dd if=/dev/zero of=/dev/block/by-name/{target}"
            result = adb_connector.execute_shell_command(cmd)
            if result is not None:
                print(f"[+] {target} wiped.")
            else:
                print(f"[-] Failed to wipe {target}.")
        else:
            print(f"[-] Partition {target} not found, skipping wipe.")
