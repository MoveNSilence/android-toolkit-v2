import subprocess
import os
import hashlib
import re

EFS_PARTITIONS = ["modemst1", "modemst2", "fsg"]

def is_safe_name(name):
    """
    Validates if a partition name is safe to use in shell commands.
    """
    return bool(re.match(r'^[a-zA-Z0-9_\-\.]+$', name))

def run_adb_command(command_list, device_ip=None):
    """
    Runs an ADB command.
    """
    cmd = ["adb"]
    if device_ip:
        cmd.extend(["-s", device_ip])
    cmd.extend(command_list)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        raise Exception(f"ADB command failed: {' '.join(cmd)}\nError: {e.stderr}")

def enable_diag_mode(device_ip):
    """
    Enables Diag Mode on the device.
    """
    print(f"[*] Enabling Diag Mode on {device_ip}...")
    try:
        run_adb_command(["shell", "setprop", "sys.usb.config", "diag,adb"], device_ip)
        print("[+] Diag Mode enabled.")
    except Exception as e:
        print(f"[-] Failed to enable Diag Mode: {e}")

def get_remote_md5(file_path, device_ip, use_su=False):
    """
    Calculates MD5 checksum of a remote file or block device on the device.
    """
    cmd = ["shell"]
    if use_su:
        cmd.extend(["su", "-c", f"md5sum {file_path}"])
    else:
        cmd.extend(["md5sum", file_path])

    output = run_adb_command(cmd, device_ip)
    return output.split()[0]

def get_remote_sha256(file_path, device_ip, use_su=False):
    """
    Calculates SHA-256 checksum of a remote file on the device.
    """
    cmd = ["shell"]
    if use_su:
        cmd.extend(["su", "-c", f"sha256sum {file_path}"])
    else:
        cmd.extend(["sha256sum", file_path])

    output = run_adb_command(cmd, device_ip)
    return output.split()[0]

def calculate_local_md5(file_path):
    """
    Calculates MD5 checksum of a local file using 64KB chunks for performance.
    """
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def calculate_local_sha256(file_path):
    """
    Calculates SHA-256 checksum of a local file using 64KB chunks for performance.
    """
    hash_sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()

def backup_efs(device_ip, backup_dir="backups"):
    """
    Backs up EFS partitions (modemst1, modemst2, fsg) with high performance.
    """
    partitions = EFS_PARTITIONS

    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)

    print(f"[*] Starting EFS backup for {device_ip}...")

    for partition in partitions:
        if not is_safe_name(partition):
            raise ValueError(f"Unsafe partition name: {partition}")

        remote_path = f"/sdcard/{partition}.img"
        # 1. Dump partition
        print(f"[*] Dumping {partition}...")
        target_partition_path = f"/dev/block/by-name/{partition}"
        dd_cmd = f"dd if={target_partition_path} of={remote_path} bs=1M conv=notrunc"
        run_adb_command(["shell", "su", "-c", dd_cmd], device_ip)

        # 2. Calculate Remote MD5
        remote_md5 = get_remote_md5(remote_path, device_ip)
        print(f"    Remote MD5: {remote_md5}")

        # 3. Pull file
        local_path = os.path.join(backup_dir, f"{partition}.img")
        print(f"[*] Pulling {partition} to {local_path}...")
        run_adb_command(["pull", remote_path, local_path], device_ip)

        # 4. Verify Local MD5
        local_md5 = calculate_local_md5(local_path)
        print(f"    Local MD5:  {local_md5}")

        if local_md5 != remote_md5:
            raise Exception(f"MD5 mismatch for {partition}! Backup corrupted.")

        # 5. Clean up remote file
        run_adb_command(["shell", "rm", remote_path], device_ip)

    print("[+] EFS Backup completed successfully.")

def wipe_efs(device_ip, backup_dir="backups"):
    """
    Wipes EFS partitions after mandatory integrity check against local backups.
    Optimized via compound ADB shell commands.
    """
    partitions = EFS_PARTITIONS

    print(f"[*] Initiating EFS Wipe for {device_ip}...")
    print("[!] WARNING: This is a destructive operation!")

    # 1. Mandatory Integrity Check
    wipe_commands = []
    for partition in partitions:
        if not is_safe_name(partition):
             raise ValueError(f"Unsafe partition name: {partition}")

        local_path = os.path.join(backup_dir, f"{partition}.img")
        if not os.path.exists(local_path):
            raise Exception(f"Backup for {partition} not found in {backup_dir}. Aborting wipe.")

        print(f"[*] Verifying integrity of {partition} before wipe...")
        local_md5 = calculate_local_md5(local_path)
        target_partition_path = f"/dev/block/by-name/{partition}"

        # Get remote MD5 of the live partition
        remote_md5 = get_remote_md5(target_partition_path, device_ip, use_su=True)

        if local_md5 != remote_md5:
            raise Exception(f"Integrity check failed for {partition}! Local backup does not match live partition.")

        wipe_commands.append(f"dd if=/dev/zero of={target_partition_path} bs=1M conv=notrunc")

    print("[+] Integrity check passed for all partitions. Proceeding with wipe.")

    # 2. Optimized Wipe execution
    compound_cmd = " && ".join(wipe_commands)
    try:
        run_adb_command(["shell", "su", "-c", compound_cmd], device_ip)
        print("[+] All partitions wiped successfully.")
    except Exception as e:
        print(f"[-] Wipe operation failed: {e}")
        raise

    print("[+] EFS Wipe completed.")

def flash_partition(device_ip, partition_name, local_image_path):
    """
    Flashes a local image to the specified partition on the device.
    """
    if not is_safe_name(partition_name):
        raise ValueError(f"Unsafe partition name: {partition_name}")

    if not os.path.exists(local_image_path):
        raise FileNotFoundError(f"Local image file not found: {local_image_path}")

    remote_temp_path = f"/sdcard/modified_{partition_name}.img"

    print(f"[*] Flashing {partition_name} on {device_ip}...")

    # 1. Push file to device
    print(f"[*] Pushing {local_image_path} to {remote_temp_path}...")
    run_adb_command(["push", local_image_path, remote_temp_path], device_ip)

    # 2. Write to partition
    target_partition_path = f"/dev/block/by-name/{partition_name}"

    print(f"[*] Writing to {target_partition_path}...")
    dd_cmd = f"dd if={remote_temp_path} of={target_partition_path} bs=1M conv=notrunc"

    try:
        # Use su -c because writing to block device usually requires root
        run_adb_command(["shell", "su", "-c", dd_cmd], device_ip)
        print(f"[+] Successfully flashed {partition_name}.")
    except Exception as e:
        print(f"[-] Failed to flash {partition_name}: {e}")
        raise

    # 3. Clean up
    print(f"[*] Cleaning up {remote_temp_path}...")
    run_adb_command(["shell", "rm", remote_temp_path], device_ip)
