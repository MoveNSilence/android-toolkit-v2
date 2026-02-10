import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Adjust path to import src
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src import god_tool

class TestMultiToolBridge(unittest.TestCase):
    def setUp(self):
        # Force InternalBlue availability for tests
        god_tool.INTERNALBLUE_AVAILABLE = True
        god_tool.ADBCore = MagicMock()

    @patch("src.god_tool.adb_connector")
    @patch("src.god_tool.modem")
    @patch("src.god_tool.injector")
    @patch("src.god_tool.os.path.exists")
    @patch("src.god_tool.shutil.copyfile")
    def test_sync_repair_success(self, mock_copy, mock_exists, mock_injector, mock_modem, mock_adb_connector):
        # Setup mocks
        mock_adb_connector.connect_to_device.return_value = True
        mock_exists.return_value = True

        # Mock InternalBlue instance
        mock_ib_instance = MagicMock()
        mock_ib_instance.connect.return_value = True
        mock_ib_instance.writeMem.return_value = True
        # Mock readMem to return the same bytes we wrote (parity check success)
        mock_ib_instance.readMem.return_value = b'\x11\x22\x33\x44\x55\x66'

        # Configure the class mock to return our instance
        god_tool.ADBCore.return_value = mock_ib_instance

        # Setup MD5 verification
        mock_modem.calculate_local_md5.return_value = "hash123"
        mock_modem.get_remote_md5.return_value = "hash123"

        # Instantiate
        bridge = god_tool.MultiToolBridge("192.168.1.55:5555")

        # Execute
        result = bridge.sync_repair(
            target_image_path="backups/modemst1.img",
            imei_offset_hex="0x100",
            imei_str="123456789012345",
            bd_addr_str="11:22:33:44:55:66",
            bd_addr_offset_hex="0x2000"
        )

        # Assertions
        self.assertTrue(result, "Sync-repair should return True on success")

        # Verify calls
        mock_adb_connector.connect_to_device.assert_called_with("192.168.1.55:5555")

        # InternalBlue Verification
        god_tool.ADBCore.assert_called_with(serial="192.168.1.55:5555")
        mock_ib_instance.connect.assert_called()
        mock_ib_instance.writeMem.assert_called_with(0x2000, b'\x11\x22\x33\x44\x55\x66')
        mock_ib_instance.readMem.assert_called_with(0x2000, 6)

        # Injector/Modem Verification
        mock_injector.inject_imei.assert_called()
        mock_modem.flash_partition.assert_called()

        # MD5 Verification
        mock_modem.calculate_local_md5.assert_called()
        mock_modem.get_remote_md5.assert_called()

        # Reboot Verification
        mock_modem.run_adb_command.assert_any_call(["reboot"], "192.168.1.55:5555")

    @patch("src.god_tool.adb_connector")
    @patch("src.god_tool.modem")
    @patch("src.god_tool.injector")
    @patch("src.god_tool.os.path.exists")
    @patch("src.god_tool.shutil.copyfile")
    def test_sync_repair_md5_fail(self, mock_copy, mock_exists, mock_injector, mock_modem, mock_adb_connector):
        # Setup mocks
        mock_adb_connector.connect_to_device.return_value = True
        mock_exists.return_value = True

        mock_ib_instance = MagicMock()
        mock_ib_instance.connect.return_value = True
        mock_ib_instance.writeMem.return_value = True
        mock_ib_instance.readMem.return_value = b'\x11\x22\x33\x44\x55\x66'
        god_tool.ADBCore.return_value = mock_ib_instance

        # Setup MD5 verification MISMATCH
        mock_modem.calculate_local_md5.return_value = "hash123"
        mock_modem.get_remote_md5.return_value = "hashBAD"

        bridge = god_tool.MultiToolBridge("192.168.1.55:5555")

        result = bridge.sync_repair(
            target_image_path="backups/modemst1.img",
            imei_offset_hex="0x100",
            imei_str="123456789012345",
            bd_addr_str="11:22:33:44:55:66",
            bd_addr_offset_hex="0x2000"
        )

        self.assertFalse(result, "Sync-repair should fail if MD5 mismatch")

        # Ensure reboot NOT called on failure (or maybe it should be? The code says return False, so no reboot)
        # Check that reboot was NOT called
        for call in mock_modem.run_adb_command.call_args_list:
            args, _ = call
            if "reboot" in args[0]:
                self.fail("Reboot should not be called if MD5 check fails")

if __name__ == "__main__":
    unittest.main()
