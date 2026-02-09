import unittest
from unittest.mock import patch, MagicMock, call
import subprocess
from src.adb_connector import ADBConnector

class TestADBConnector(unittest.TestCase):
    def setUp(self):
        self.connector = ADBConnector()

    @patch('src.adb_connector.subprocess.run')
    def test_check_su_access_success(self, mock_run):
        mock_run.return_value = MagicMock(stdout='uid=0(root) gid=0(root) groups=0(root)\n', returncode=0)
        self.assertTrue(self.connector.check_su_access())
        mock_run.assert_called_with(['adb', 'shell', 'su', '-c', 'id'], capture_output=True, text=True, check=True)

    @patch('src.adb_connector.subprocess.run')
    def test_check_su_access_failure(self, mock_run):
        mock_run.return_value = MagicMock(stdout='uid=2000(shell) gid=2000(shell)\n', returncode=0)
        self.assertFalse(self.connector.check_su_access())

    @patch('src.adb_connector.subprocess.run')
    def test_identify_block_device_path_success(self, mock_run):
        # Simulate failure for first path, success for second
        def side_effect(cmd, **kwargs):
            # cmd is like ['adb', 'shell', 'ls', '/path/']
            # checking if '/dev/block/bootdevice/by-name/' is in the command list
            if '/dev/block/bootdevice/by-name/' in cmd:
                 raise subprocess.CalledProcessError(1, cmd)
            if '/dev/block/platform/msm_sdcc.1/by-name/' in cmd:
                 return MagicMock(stdout='', returncode=0)
            return MagicMock(stdout='', returncode=0)

        mock_run.side_effect = side_effect

        path = self.connector.identify_block_device_path()
        self.assertEqual(path, '/dev/block/platform/msm_sdcc.1/by-name/')

    @patch('src.adb_connector.subprocess.run')
    def test_identify_block_device_path_failure(self, mock_run):
        mock_run.side_effect = subprocess.CalledProcessError(1, 'ls')
        with self.assertRaises(RuntimeError):
            self.connector.identify_block_device_path()

    @patch('src.adb_connector.ADBConnector.identify_block_device_path')
    @patch('src.adb_connector.ADBConnector.check_su_access')
    @patch('src.adb_connector.subprocess.run')
    def test_wipe_modem_partitions(self, mock_run, mock_check_su, mock_identify):
        mock_check_su.return_value = True
        mock_identify.return_value = '/dev/block/bootdevice/by-name/'
        mock_run.return_value = MagicMock(stdout='', returncode=0)

        self.connector.wipe_modem_partitions()

        expected_calls = []
        partitions = ['modemst1', 'modemst2', 'fsg', 'fsc']
        for part in partitions:
             expected_calls.append(call(
                 ['adb', 'shell', 'su', '-c', f'dd if=/dev/zero of=/dev/block/bootdevice/by-name/{part}'],
                 capture_output=True, text=True, check=True
             ))

        mock_run.assert_has_calls(expected_calls, any_order=True)
        self.assertEqual(mock_run.call_count, 4)

    @patch('src.adb_connector.subprocess.run')
    def test_reboot_device(self, mock_run):
        self.connector.reboot_device()
        mock_run.assert_called_with(['adb', 'reboot'], check=True)

if __name__ == '__main__':
    unittest.main()
