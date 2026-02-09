import subprocess
import sys
import argparse
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ADBConnector:
    def __init__(self, device_id=None):
        self.device_id = device_id
        self.adb_cmd = ['adb']
        if device_id:
            self.adb_cmd.extend(['-s', device_id])

    def execute_command(self, command_parts):
        """Executes an ADB shell command.

        Args:
            command_parts (list): List of command strings to execute in adb shell.
        """
        full_cmd = self.adb_cmd + ['shell'] + command_parts
        logger.debug(f"Executing: {' '.join(full_cmd)}")
        try:
            result = subprocess.run(full_cmd, capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed: {e}")
            logger.error(f"Stderr: {e.stderr}")
            raise

    def check_su_access(self):
        """Checks if su is available and we can get root."""
        try:
            # Try to run 'id' with su
            output = self.execute_command(['su', '-c', 'id'])
            if 'uid=0(root)' in output:
                return True
            return False
        except subprocess.CalledProcessError:
            return False

    def identify_block_device_path(self):
        """Identifies the correct block device path."""
        paths_to_check = [
            "/dev/block/bootdevice/by-name/",  # Motorola/Generic
            "/dev/block/platform/msm_sdcc.1/by-name/", # Samsung
            "/dev/block/by-name/" # Common fallback
        ]

        for path in paths_to_check:
            try:
                # Check if path exists by listing it.
                # We interpret a successful ls as existence.
                self.execute_command(['ls', path])
                logger.info(f"Found block device path: {path}")
                return path
            except subprocess.CalledProcessError:
                # ls failed, likely path doesn't exist
                continue

        raise RuntimeError("Could not identify block device path.")

    def wipe_partition(self, partition_name, block_path):
        """Wipes a specific partition using dd."""
        target_path = f"{block_path}{partition_name}"
        logger.info(f"Wiping {partition_name} at {target_path}...")

        # Construct the dd command.
        # using if=/dev/zero of=TARGET
        dd_cmd = f"dd if=/dev/zero of={target_path}"

        # Wrap in su
        cmd = ['su', '-c', dd_cmd]

        try:
            self.execute_command(cmd)
            logger.info(f"Successfully wiped {partition_name}.")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to wipe {partition_name}: {e}")
            # We re-raise or handle depending on desired strictness.
            # Usually if one fails, we might want to continue or stop.
            # User instructions imply we just do all of them.
            raise

    def wipe_modem_partitions(self):
        """Wipes modemst1, modemst2, fsg, fsc."""
        logger.info("Checking for SU access...")
        if not self.check_su_access():
            logger.error("Root access (su) is required but not available on the device.")
            sys.exit(1)

        try:
            block_path = self.identify_block_device_path()
        except RuntimeError as e:
            logger.error(str(e))
            sys.exit(1)

        partitions = ['modemst1', 'modemst2', 'fsg', 'fsc']
        for part in partitions:
            try:
                self.wipe_partition(part, block_path)
            except subprocess.CalledProcessError:
                logger.warning(f"Could not wipe {part}. Proceeding to next.")

    def reboot_device(self):
        """Reboots the device."""
        logger.info("Rebooting device...")
        try:
            subprocess.run(self.adb_cmd + ['reboot'], check=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to reboot: {e}")

def main():
    parser = argparse.ArgumentParser(description="ADB Connector Toolkit")
    parser.add_argument('--wipe-efs', action='store_true', help="Wipe EFS/Modem partitions (modemst1, modemst2, fsg, fsc)")
    parser.add_argument('--device', help="Target specific device ID")

    args = parser.parse_args()

    connector = ADBConnector(device_id=args.device)

    if args.wipe_efs:
        connector.wipe_modem_partitions()
        connector.reboot_device()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
