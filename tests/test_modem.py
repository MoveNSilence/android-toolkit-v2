import sys
import os
import unittest
import tempfile
import hashlib
from unittest.mock import patch, MagicMock

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.modem import backup_efs, wipe_efs, enable_diag_mode, calculate_local_md5

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

    def test_calculate_local_md5_standard(self):
        content = b"hello world"
        expected_md5 = hashlib.md5(content).hexdigest()

        with tempfile.NamedTemporaryFile(delete=False) as tf:
            tf.write(content)
            temp_name = tf.name

        try:
            result = calculate_local_md5(temp_name)
            self.assertEqual(result, expected_md5)
        finally:
            if os.path.exists(temp_name):
                os.remove(temp_name)

    def test_calculate_local_md5_empty(self):
        content = b""
        expected_md5 = hashlib.md5(content).hexdigest()

        with tempfile.NamedTemporaryFile(delete=False) as tf:
            tf.write(content)
            temp_name = tf.name

        try:
            result = calculate_local_md5(temp_name)
            self.assertEqual(result, expected_md5)
        finally:
            if os.path.exists(temp_name):
                os.remove(temp_name)

    def test_calculate_local_md5_large(self):
        # Create content larger than the 4096 byte chunk size
        content = b"A" * 5000
        expected_md5 = hashlib.md5(content).hexdigest()

        with tempfile.NamedTemporaryFile(delete=False) as tf:
            tf.write(content)
            temp_name = tf.name

        try:
            result = calculate_local_md5(temp_name)
            self.assertEqual(result, expected_md5)
        finally:
            if os.path.exists(temp_name):
                os.remove(temp_name)

    def test_calculate_local_md5_missing(self):
        with self.assertRaises(FileNotFoundError):
            calculate_local_md5("non_existent_file_path_12345")

if __name__ == "__main__":
    unittest.main()
