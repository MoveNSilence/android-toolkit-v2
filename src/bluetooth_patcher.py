import hashlib
import time
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

try:
    from internalblue.adbcore import ADBCore
except ImportError:
    logger.error("InternalBlue not found. Please install it using pip.")
    sys.exit(1)

class BluetoothPatcher:
    def __init__(self, log_level='info'):
        """
        Initializes the BluetoothPatcher with an ADBCore instance.
        """
        self.core = ADBCore(log_level=log_level)
        self.monitoring = False
        self.lmp_packet_count = 0
        self.last_lmp_packet_time = 0

    def connect(self, device_id=None):
        """
        Connects to the specified Android device via ADB.
        If device_id is None, connects to the first available device.
        """
        devices = self.core.device_list()
        if not devices:
            logger.error("No ADB devices found.")
            return False

        target_device = None
        if device_id:
            for d in devices:
                # device_list returns [(serial, interface), ...]
                if d[0] == device_id:
                    target_device = d
                    break
            if not target_device:
                logger.error(f"Device {device_id} not found in ADB list: {[d[0] for d in devices]}")
                return False
        else:
            target_device = devices[0]

        # Use the target device
        self.core.interface = target_device[1]

        if not self.core.connect():
            logger.error(f"Failed to connect to InternalBlue via ADB on {target_device[0]}.")
            return False

        logger.info(f"Connected to InternalBlue on {target_device[0]} successfully.")
        return True

    def read_ram(self, address, size):
        """
        Reads 'size' bytes from the specified memory address.
        """
        return self.core.readMem(address, size)

    def write_ram(self, address, data):
        """
        Writes 'data' (bytes) to the specified memory address.
        """
        return self.core.writeMem(address, data)

    def verify_ram(self, address, expected_data):
        """
        Reads back memory from 'address' and compares it with 'expected_data'.
        Returns True if they match, False otherwise.
        """
        read_data = self.read_ram(address, len(expected_data))
        if read_data != expected_data:
            logger.error(f"Verification failed! Expected: {expected_data.hex()}, Got: {read_data.hex() if read_data else 'None'}")
            return False
        return True

    def calculate_md5(self, data):
        """
        Calculates the MD5 checksum of the given data.
        """
        return hashlib.md5(data).hexdigest()

    def _lmp_monitor_callback(self, record):
        """
        Callback for HCI events. Monitors for LMP packets.
        """
        # InternalBlue record format: (h4_type, data, timestamp, original_len, inc_len)
        # h4_type: 1=CMD, 2=ACL, 3=SCO, 4=EVT

        # We update the timestamp to indicate the radio is active.
        self.lmp_packet_count += 1
        self.last_lmp_packet_time = time.time()

        # In a real implementation, we would parse 'data' to identify LMP packets
        # specifically if diagnostic logging is enabled.
        # For now, any HCI activity is a sign of life.

    def start_lmp_monitor(self):
        """
        Starts the LMP monitor.
        """
        self.monitoring = True
        self.lmp_packet_count = 0
        self.last_lmp_packet_time = time.time()

        # Enable diagnostic logging (Broadcom specific, but harmless if not supported or implemented in core)
        # self.core.enableBroadcomDiagnosticLogging(True)

        self.core.registerHciCallback(self._lmp_monitor_callback)
        logger.info("LMP Monitor started.")

    def stop_lmp_monitor(self):
        """
        Stops the LMP monitor.
        """
        self.monitoring = False
        self.core.unregisterHciCallback(self._lmp_monitor_callback)
        # self.core.enableBroadcomDiagnosticLogging(False)
        logger.info("LMP Monitor stopped.")

    def is_radio_stable(self, timeout=10):
        """
        Checks if the radio is stable.
        Returns True if packets have been received within the timeout.
        """
        if time.time() - self.last_lmp_packet_time > timeout:
             logger.warning(f"Radio instability detected: No packets for {timeout} seconds.")
             return False
        return True
