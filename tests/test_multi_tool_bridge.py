import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Ensure src is in path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.multi_tool_bridge import MultiToolBridge

class TestMultiToolBridge(unittest.TestCase):
    @patch('src.multi_tool_bridge.ADBCore')
    def test_initialize_shared_bridge_success(self, mock_adb_core):
        # Setup mock
        mock_instance = mock_adb_core.return_value
        mock_instance.connect.return_value = True

        bridge = MultiToolBridge(device_id="device123")
        result = bridge.initialize_shared_bridge()

        # Verify
        mock_adb_core.assert_called_with(serial="device123")
        mock_instance.connect.assert_called_once()
        self.assertEqual(result, mock_instance)
        self.assertEqual(bridge.ib_core, mock_instance)

    @patch('src.multi_tool_bridge.ADBCore')
    def test_initialize_shared_bridge_failure(self, mock_adb_core):
        # Setup mock
        mock_instance = mock_adb_core.return_value
        mock_instance.connect.return_value = False

        bridge = MultiToolBridge(device_id="device123")
        result = bridge.initialize_shared_bridge()

        # Verify
        mock_instance.connect.assert_called_once()
        self.assertIsNone(result)

    @patch('subprocess.check_output')
    def test_execute_god_tool_cmd(self, mock_check_output):
        bridge = MultiToolBridge(device_id="device123")
        command = "ls -l"
        expected_output = b"file1\nfile2"
        mock_check_output.return_value = expected_output

        output = bridge.execute_god_tool_cmd(command)

        # Verify
        # This checks the improved implementation using list construction
        mock_check_output.assert_called_once_with(['adb', '-s', 'device123', 'shell', 'ls -l'])
        self.assertEqual(output, expected_output)

    @patch('subprocess.check_output')
    def test_execute_god_tool_cmd_no_device_id(self, mock_check_output):
        bridge = MultiToolBridge()
        command = "ls -l"
        expected_output = b"file1\nfile2"
        mock_check_output.return_value = expected_output

        output = bridge.execute_god_tool_cmd(command)

        # Verify
        # This checks the improved implementation without device_id
        mock_check_output.assert_called_once_with(['adb', 'shell', 'ls -l'])
        self.assertEqual(output, expected_output)

if __name__ == '__main__':
    unittest.main()
