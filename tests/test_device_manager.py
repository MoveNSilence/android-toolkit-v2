import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

import device_manager

class TestDeviceManager(unittest.TestCase):

    @patch('adb_connector.connect_to_device')
    @patch('adb_connector.execute_shell_command')
    @patch('adb_connector.pull_file')
    def test_backup_partitions(self, mock_pull, mock_exec, mock_connect):
        # Decorators applied bottom-up, arguments passed bottom-up.
        # mock_pull (bottom), mock_exec (middle), mock_connect (top)

        mock_connect.return_value = True
        mock_pull.return_value = True

        def exec_side_effect(cmd):
            if "ls -l" in cmd:
                return "modemst1 -> /dev/block/mmcblk0p1\nmodemst2 -> /dev/block/mmcblk0p2\nefs -> /dev/block/mmcblk0p3\nother -> /dev/block/mmcblk0p4"
            # Simulate success for other commands
            return ""

        mock_exec.side_effect = exec_side_effect

        device_manager.backup_partitions("192.168.1.1:5555")

        # Verify connect called
        mock_connect.assert_called_with("192.168.1.1:5555")

        # Verify execute calls
        # 1 list + 3 dd + 3 rm = 7 calls
        self.assertEqual(mock_exec.call_count, 7)

        calls = [c[0][0] for c in mock_exec.call_args_list]

        # Check dd commands
        dd_calls = [c for c in calls if "dd if=" in c]
        self.assertEqual(len(dd_calls), 3)
        self.assertTrue(any("modemst1" in c for c in dd_calls))
        self.assertTrue(any("modemst2" in c for c in dd_calls))
        self.assertTrue(any("efs" in c for c in dd_calls))

        # Check pull calls
        self.assertEqual(mock_pull.call_count, 3)

    @patch('adb_connector.connect_to_device')
    @patch('adb_connector.execute_shell_command')
    def test_wipe_partitions(self, mock_exec, mock_connect):
        # mock_exec (bottom), mock_connect (top)
        mock_connect.return_value = True

        def exec_side_effect(cmd):
            if "ls -l" in cmd:
                # Include efs to make sure it is NOT wiped
                return "modemst1 -> /dev/block/mmcblk0p1\nmodemst2 -> /dev/block/mmcblk0p2\nefs -> /dev/block/mmcblk0p3"
            return ""

        mock_exec.side_effect = exec_side_effect

        device_manager.wipe_security_partitions("192.168.1.1:5555")

        # Verify connect
        mock_connect.assert_called_with("192.168.1.1:5555")

        # Verify calls
        # 1 list + 2 wipes = 3 calls
        self.assertEqual(mock_exec.call_count, 3)

        calls = [c[0][0] for c in mock_exec.call_args_list]

        # Check wipe commands
        wipe_calls = [c for c in calls if "dd if=/dev/zero" in c]
        self.assertEqual(len(wipe_calls), 2)
        self.assertTrue(any("modemst1" in c for c in wipe_calls))
        self.assertTrue(any("modemst2" in c for c in wipe_calls))
        # Ensure efs was NOT wiped
        self.assertFalse(any("efs" in c for c in wipe_calls))

if __name__ == '__main__':
    unittest.main()
