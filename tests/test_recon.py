import unittest
from unittest.mock import patch, MagicMock, call
import os
import sys

# Add src to path so we can import adb_connector
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

import adb_connector

class TestRecon(unittest.TestCase):
    def setUp(self):
        # Create dummy modemst1.img
        self.test_img = "modemst1.img"
        with open(self.test_img, "wb") as f:
            # Random data
            f.write(b'\x00' * 100)

            # Valid IMEI: 355866050456784 (Luhn valid)
            # 3, 5*2=10->1, 5, 8*2=16->7, 6, 6*2=12->3, 0, 5*2=10->1, 0, 4*2=8, 5, 6*2=12->3, 7, 8*2=16->7, 4
            # Sum: 3+1+5+7+6+3+0+1+0+8+5+3+7+7+4 = 60. Valid.
            self.valid_imei = b'355866050456784'
            f.write(self.valid_imei)

            f.write(b'\x00' * 50)

            # Invalid IMEI (Luhn check fails): 123456789012345
            self.invalid_imei = b'123456789012345'
            f.write(self.invalid_imei)

            f.write(b'\x00' * 50)

            # Hex patterns
            # 0x088A at offset 100 + 15 + 50 + 15 + 50 = 230?
            # 100 + 15 = 115
            # 115 + 50 = 165
            # 165 + 15 = 180
            # 180 + 50 = 230
            f.write(b'\x08\x8A\x11\x22') # NV Item 550 marker 1
            f.write(b'\x00' * 10)
            f.write(b'\x08\x3A\x33\x44') # NV Item 550 marker 2

    def tearDown(self):
        if os.path.exists(self.test_img):
            os.remove(self.test_img)
        if os.path.exists("recon_report.txt"):
            os.remove("recon_report.txt")

    def test_luhn_checksum(self):
        # Test valid
        self.assertTrue(adb_connector.luhn_checksum("355866050456784"))
        self.assertTrue(adb_connector.luhn_checksum("79927398713"))
        # Test invalid
        self.assertFalse(adb_connector.luhn_checksum("123456789012345"))
        self.assertFalse(adb_connector.luhn_checksum("355866050456783"))
        # Test non-digits
        self.assertFalse(adb_connector.luhn_checksum("abc"))

    @patch('adb_connector.subprocess.run')
    def test_dump_partitions(self, mock_run):
        mock_run.return_value.stdout = ""
        mock_run.return_value.returncode = 0

        adb_connector.dump_partitions()

        # Verify calls
        expected_calls = [
            call(["adb", "shell", "su", "-c", "dd if=/dev/block/by-name/modemst1 of=/sdcard/modemst1.img"], capture_output=True, text=True, check=True),
            call(["adb", "shell", "su", "-c", "dd if=/dev/block/by-name/modemst2 of=/sdcard/modemst2.img"], capture_output=True, text=True, check=True),
            call(["adb", "shell", "su", "-c", "dd if=/dev/block/by-name/fsg of=/sdcard/fsg.img"], capture_output=True, text=True, check=True)
        ]
        mock_run.assert_has_calls(expected_calls, any_order=True)

    @patch('adb_connector.subprocess.run')
    def test_pull_images(self, mock_run):
        mock_run.return_value.returncode = 0

        adb_connector.pull_images()

        expected_calls = [
            call(["adb", "pull", "/sdcard/modemst1.img", "."], capture_output=True, text=True, check=True),
            call(["adb", "pull", "/sdcard/modemst2.img", "."], capture_output=True, text=True, check=True),
            call(["adb", "pull", "/sdcard/fsg.img", "."], capture_output=True, text=True, check=True)
        ]
        mock_run.assert_has_calls(expected_calls, any_order=True)

    def test_analyze_image(self):
        # We need to make sure the function actually runs and produces output
        # Since analyze_image is supposed to return results or write to file,
        # we can check return values or file content.
        # Assuming it returns a dict or list of findings for testability,
        # but the requirement says "Generate a recon_report.txt".

        findings = adb_connector.analyze_image(self.test_img)

        # Check findings
        # Expecting valid IMEI found
        self.assertIn("355866050456784", str(findings))

        # Expecting Hex patterns found
        # 0x088A
        self.assertTrue(any("0x088a" in str(f).lower() for f in findings))
        # 0x083A
        self.assertTrue(any("0x083a" in str(f).lower() for f in findings))

    @patch('adb_connector.generate_report')
    @patch('adb_connector.dump_partitions')
    @patch('adb_connector.pull_images')
    @patch('adb_connector.analyze_image')
    @patch('adb_connector.connect_to_device')
    def test_main_integration(self, mock_connect, mock_analyze, mock_pull, mock_dump, mock_generate_report):
        mock_connect.return_value = True

        # We need to simulate arguments passed to main
        with patch('sys.argv', ['adb_connector.py', '192.168.1.1:5555']):
            adb_connector.main()

        mock_connect.assert_called_once()
        mock_dump.assert_called_once()
        mock_pull.assert_called_once()
        mock_analyze.assert_called()
        mock_generate_report.assert_called()

if __name__ == '__main__':
    unittest.main()
