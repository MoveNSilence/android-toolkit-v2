import unittest
import subprocess
from unittest.mock import patch, MagicMock
from src.modem import backup_efs, wipe_efs, enable_diag_mode, get_remote_md5

class TestModem(unittest.TestCase):

    @patch("src.modem.subprocess.run")
    @patch("src.modem.os.path.exists")
    @patch("src.modem.os.makedirs")
    @patch("src.modem.calculate_local_md5")
    def test_backup_efs_success(self, mock_calc_md5, mock_makedirs, mock_exists, mock_run):
        # Setup mocks
        mock_exists.return_value = False # Directory doesn't exist, create it
        mock_calc_md5.return_value = "d41d8cd98f00b204e9800998ecf8427e" # Dummy MD5

        # Mock subprocess.run return values based on call args
        def side_effect(*args, **kwargs):
            cmd = args[0]
            if "md5sum" in cmd:
                return MagicMock(stdout="d41d8cd98f00b204e9800998ecf8427e  /sdcard/modemst1.img\n")
            return MagicMock(stdout="")

        mock_run.side_effect = side_effect

        backup_efs("192.168.1.1:5555")

        # Verify calls
        self.assertTrue(mock_makedirs.called)
        self.assertTrue(mock_run.called)
        # Verify dd called for 3 partitions
        # Verify md5sum called for 3 partitions
        # Verify pull called for 3 partitions
        # Verify rm called for 3 partitions
        self.assertEqual(mock_run.call_count, 4 * 3)

    @patch("src.modem.subprocess.run")
    @patch("src.modem.os.path.exists")
    def test_wipe_efs_missing_backup(self, mock_exists, mock_run):
        mock_exists.return_value = False # Backup missing

        with self.assertRaises(Exception) as context:
            wipe_efs("192.168.1.1:5555")

        self.assertIn("Backup for modemst1 not found", str(context.exception))
        self.assertFalse(mock_run.called) # Should not run dd if backup missing

    @patch("src.modem.subprocess.run")
    @patch("src.modem.os.path.exists")
    def test_wipe_efs_success(self, mock_exists, mock_run):
        mock_exists.return_value = True # Backup exists

        wipe_efs("192.168.1.1:5555")

        self.assertTrue(mock_run.called)
        # Verify dd if=/dev/zero called 3 times
        self.assertEqual(mock_run.call_count, 3)

    @patch("src.modem.subprocess.run")
    def test_enable_diag_mode(self, mock_run):
        enable_diag_mode("192.168.1.1:5555")
        mock_run.assert_called_with(
            ["adb", "-s", "192.168.1.1:5555", "shell", "setprop", "sys.usb.config", "diag,adb"],
            capture_output=True, text=True, check=True
        )

    @patch("src.modem.subprocess.run")
    def test_get_remote_md5_formats(self, mock_run):
        # Case 1: "hash  filepath" (Toybox/Busybox standard)
        mock_run.return_value = MagicMock(stdout="d41d8cd98f00b204e9800998ecf8427e  /sdcard/file\n")
        md5 = get_remote_md5("/sdcard/file", "192.168.1.1:5555")
        self.assertEqual(md5, "d41d8cd98f00b204e9800998ecf8427e")

        # Case 2: "hash" (some custom md5sum implementations)
        mock_run.return_value = MagicMock(stdout="d41d8cd98f00b204e9800998ecf8427e\n")
        md5 = get_remote_md5("/sdcard/file", "192.168.1.1:5555")
        self.assertEqual(md5, "d41d8cd98f00b204e9800998ecf8427e")

    @patch("src.modem.subprocess.run")
    def test_get_remote_md5_adb_failure(self, mock_run):
        # Simulate ADB command failure
        mock_run.side_effect = subprocess.CalledProcessError(1, "adb shell md5sum", stderr="File not found")

        with self.assertRaises(Exception) as context:
            get_remote_md5("/sdcard/nonexistent", "192.168.1.1:5555")

        self.assertIn("ADB command failed", str(context.exception))

if __name__ == "__main__":
    unittest.main()
