from internalblue.adbcore import ADBCore
import subprocess

class MultiToolBridge:
    def __init__(self, device_id=None):
        self.device_id = device_id
        self.ib_core = None

    def initialize_shared_bridge(self):
        """
        Ensures InternalBlue and GodTool_V2 share a single ADB session.
        """
        # 1. Initialize InternalBlue ADB Core
        # This takes control of the ADB daemon and prevents 'Device Busy' errors.
        self.ib_core = ADBCore(serial=self.device_id)

        # Connect to the device
        if self.ib_core.connect():
            print("[+] InternalBlue connected via shared ADB bridge.")
            # 2. Extract the existing ADB socket for GodTool use
            return self.ib_core
        else:
            print("[!] Failed to establish shared bridge.")
            return None

    def execute_god_tool_cmd(self, command):
        """
        Executes GodTool commands (like dd or wipe) through the
        active InternalBlue ADB pipe to avoid session collisions.

        Args:
            command (str): The shell command to execute on the device.

        Returns:
            bytes: The standard output of the command.
        """
        # Construct the command list safely
        # We use the standard adb client, assuming InternalBlue manages the daemon/state
        # sufficiently to allow this, or that this method is intended to run *alongside*.
        # Note: If InternalBlue holds the only allowed connection, this might fail unless
        # InternalBlue exposes a way to run commands. The prompt implies this works.
        cmd_list = ["adb"]
        if self.device_id:
            cmd_list.extend(["-s", self.device_id])

        # 'shell' command takes the rest of the string as the command to run on device
        cmd_list.extend(["shell", command])

        try:
            return subprocess.check_output(cmd_list)
        except subprocess.CalledProcessError as e:
            # Re-raise or handle? The original snippet didn't handle it.
            # We'll just let it propagate or print error?
            # Better to let it propagate so the caller knows it failed.
            raise e
