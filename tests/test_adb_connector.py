import sys
import os
import unittest
import subprocess
from unittest.mock import patch, MagicMock

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.adb_connector import connect_to_device, check_adb_installed

class TestAdbConnector(unittest.TestCase):
    @patch('src.adb_connector.subprocess.run')
    def test_check_adb_installed_success(self, mock_run):
        # Mock subprocess.run to succeed
        mock_run.return_value = MagicMock()
        self.assertTrue(check_adb_installed())
        mock_run.assert_called_with(["adb", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    @patch('src.adb_connector.subprocess.run')
    def test_check_adb_installed_failure(self, mock_run):
        # Mock subprocess.run to raise FileNotFoundError
        mock_run.side_effect = FileNotFoundError
        self.assertFalse(check_adb_installed())
        mock_run.assert_called_with(["adb", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    @patch('src.adb_connector.check_adb_installed')
    @patch('src.adb_connector.subprocess.run')
    def test_connect_success(self, mock_run, mock_check_adb):
        # Mock ADB check as successful
        mock_check_adb.return_value = True

        # Mock successful connection output
        mock_result = MagicMock()
        mock_result.stdout = "connected to 10.0.0.193:43261"
        mock_run.return_value = mock_result

        self.assertTrue(connect_to_device("10.0.0.193:43261"))

        # Verify connect command was called
        mock_run.assert_called_with(["adb", "connect", "10.0.0.193:43261"], capture_output=True, text=True)

    @patch('src.adb_connector.check_adb_installed')
    @patch('src.adb_connector.subprocess.run')
    def test_connect_failure(self, mock_run, mock_check_adb):
        # Mock ADB check as successful
        mock_check_adb.return_value = True

        # Mock failed connection output
        mock_result = MagicMock()
        mock_result.stdout = "unable to connect to 10.0.0.193:43261"
        mock_run.return_value = mock_result

        self.assertFalse(connect_to_device("10.0.0.193:43261"))

    @patch('src.adb_connector.check_adb_installed')
    def test_adb_not_installed(self, mock_check_adb):
        # Mock ADB check as failed
        mock_check_adb.return_value = False

        self.assertFalse(connect_to_device("10.0.0.193:43261"))

    @patch('src.adb_connector.check_adb_installed')
    @patch('src.adb_connector.subprocess.run')
    def test_connect_to_device_unexpected_error(self, mock_run, mock_check_adb):
        # Mock ADB check as successful
        mock_check_adb.return_value = True
        # Mock subprocess.run to raise an unexpected Exception
        mock_run.side_effect = Exception("Unexpected error")

        self.assertFalse(connect_to_device("10.0.0.193:43261"))
