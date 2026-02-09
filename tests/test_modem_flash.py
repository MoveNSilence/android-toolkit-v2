import unittest
from unittest.mock import patch, MagicMock
from src.modem import flash_partition
import os

class TestModemFlash(unittest.TestCase):
    def setUp(self):
        self.filename = "test_flash.img"
        with open(self.filename, "wb") as f:
            f.write(b"dummy data")

    def tearDown(self):
        if os.path.exists(self.filename):
            os.remove(self.filename)

    @patch("src.modem.run_adb_command")
    def test_flash_partition_success(self, mock_run_adb):
        device_ip = "192.168.1.1:5555"
        partition = "modemst1"

        flash_partition(device_ip, partition, self.filename)

        # Verify calls
        # 1. Push
        remote_temp_path = f"/sdcard/modified_{partition}.img"
        mock_run_adb.assert_any_call(["push", self.filename, remote_temp_path], device_ip)

        # 2. dd
        target_partition_path = f"/dev/block/by-name/{partition}"
        dd_cmd = f"dd if={remote_temp_path} of={target_partition_path}"
        mock_run_adb.assert_any_call(["shell", "su", "-c", dd_cmd], device_ip)

        # 3. Clean up
        mock_run_adb.assert_any_call(["shell", "rm", remote_temp_path], device_ip)

    def test_flash_partition_file_not_found(self):
         with self.assertRaises(FileNotFoundError):
             flash_partition("ip", "part", "nonexistent.img")

if __name__ == "__main__":
    unittest.main()
