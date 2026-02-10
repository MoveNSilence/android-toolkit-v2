import subprocess
import os
import hashlib

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

def get_remote_md5(file_path, device_ip):
    """
    Calculates MD5 checksum of a remote file on the device.
    """
    output = run_adb_command(["shell", "md5sum", file_path], device_ip)
    # Output format: "hash  filepath" or just "hash" depending on toybox/busybox
    # Usually: "d41d8cd98f00b204e9800998ecf8427e  /sdcard/file"
    return output.split()[0]

def calculate_local_md5(file_path):
    """
    Calculates MD5 checksum of a local file.
    """
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def backup_efs(device_ip, backup_dir="backups"):
    """
    Backs up EFS partitions (modemst1, modemst2, fsg).
    """
    partitions = ["modemst1", "modemst2", "fsg"]

    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)

    print(f"[*] Starting EFS backup for {device_ip}...")

    for partition in partitions:
        remote_path = f"/sdcard/{partition}.img"
        # 1. Dump partition
        print(f"[*] Dumping {partition}...")
        # Note: Partition path might vary. Assuming /dev/block/bootdevice/by-name/
        # Checks if we should look up the path first?
        # For now, use the standard Qualcomm path.
        dd_cmd = f"dd if=/dev/block/bootdevice/by-name/{partition} of={remote_path}"
        run_adb_command(["shell", dd_cmd], device_ip)

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
    Wipes EFS partitions after verifying backup.
    """
    partitions = ["modemst1", "modemst2", "fsg"]

    print(f"[*] Initiating EFS Wipe for {device_ip}...")
    print("[!] WARNING: This is a destructive operation!")

    # 1. Verify Backups Exist
    for partition in partitions:
        local_path = os.path.join(backup_dir, f"{partition}.img")
        if not os.path.exists(local_path):
            raise Exception(f"Backup for {partition} not found in {backup_dir}. Aborting wipe.")
        # Optional: Verify backup integrity again? Maybe too slow.

    print("[+] Backups verified. Proceeding with wipe.")

    for partition in partitions:
        print(f"[*] Wiping {partition}...")
        # wipe using dd from /dev/zero
        dd_cmd = f"dd if=/dev/zero of=/dev/block/bootdevice/by-name/{partition}"
        try:
            run_adb_command(["shell", dd_cmd], device_ip)
            print(f"[+] Wiped {partition}.")
        except Exception as e:
             print(f"[-] Failed to wipe {partition}: {e}")
             raise

    print("[+] EFS Wipe completed.")

def flash_partition(device_ip, partition_name, local_image_path):
    """
    Flashes a local image to the specified partition on the device.
    """
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
    dd_cmd = f"dd if={remote_temp_path} of={target_partition_path}"

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
