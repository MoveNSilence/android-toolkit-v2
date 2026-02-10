import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Ensure src is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.bluetooth_patcher import BluetoothPatcher

class TestBluetoothPatcher(unittest.TestCase):
    def setUp(self):
        # Patch ADBCore at the class level or inside setup
        self.patcher = patch('src.bluetooth_patcher.ADBCore')
        self.mock_adb_core = self.patcher.start()

        # Setup mock behavior
        self.mock_core_instance = self.mock_adb_core.return_value
        self.mock_core_instance.device_list.return_value = [('device1', 'device_serial')]
        self.mock_core_instance.connect.return_value = True

        self.bp = BluetoothPatcher()

    def tearDown(self):
        self.patcher.stop()

    def test_connect_success(self):
        self.assertTrue(self.bp.connect())
        self.mock_core_instance.connect.assert_called_once()
        self.assertEqual(self.mock_core_instance.interface, 'device_serial')

    def test_connect_specific_device(self):
        self.mock_core_instance.device_list.return_value = [('other_device', 'other_serial'), ('target_device', 'target_serial')]
        self.assertTrue(self.bp.connect(device_id='target_device'))
        self.assertEqual(self.mock_core_instance.interface, 'target_serial')

    def test_connect_specific_device_not_found(self):
        self.mock_core_instance.device_list.return_value = [('other_device', 'other_serial')]
        self.assertFalse(self.bp.connect(device_id='target_device'))

    def test_connect_failure_no_devices(self):
        self.mock_core_instance.device_list.return_value = []
        self.assertFalse(self.bp.connect())

    def test_connect_failure_adb_error(self):
        self.mock_core_instance.connect.return_value = False
        self.assertFalse(self.bp.connect())

    def test_read_ram(self):
        self.bp.read_ram(0x1000, 10)
        self.mock_core_instance.readMem.assert_called_with(0x1000, 10)

    def test_write_ram(self):
        data = b'\x01\x02\x03'
        self.bp.write_ram(0x2000, data)
        self.mock_core_instance.writeMem.assert_called_with(0x2000, data)

    def test_verify_ram_success(self):
        expected = b'\xAA\xBB'
        self.mock_core_instance.readMem.return_value = expected
        self.assertTrue(self.bp.verify_ram(0x3000, expected))

    def test_verify_ram_failure(self):
        expected = b'\xAA\xBB'
        self.mock_core_instance.readMem.return_value = b'\xCC\xDD'
        self.assertFalse(self.bp.verify_ram(0x3000, expected))

    def test_calculate_md5(self):
        data = b'test'
        expected_md5 = '098f6bcd4621d373cade4e832627b4f6'
        self.assertEqual(self.bp.calculate_md5(data), expected_md5)

    def test_lmp_monitor(self):
        self.bp.start_lmp_monitor()
        self.mock_core_instance.registerHciCallback.assert_called_once()
        self.assertTrue(self.bp.monitoring)

        self.bp.stop_lmp_monitor()
        self.mock_core_instance.unregisterHciCallback.assert_called_once()
        self.assertFalse(self.bp.monitoring)

    def test_is_radio_stable_failure(self):
        # Mock time.time()
        with patch('src.bluetooth_patcher.time.time') as mock_time:
             mock_time.side_effect = [1000, 1020, 1030, 1040]
             self.bp.start_lmp_monitor()
             self.assertFalse(self.bp.is_radio_stable(timeout=10))

    def test_is_radio_stable_success(self):
        with patch('src.bluetooth_patcher.time.time') as mock_time:
             mock_time.side_effect = [1000, 1005, 1006, 1007]
             self.bp.start_lmp_monitor()
             self.assertTrue(self.bp.is_radio_stable(timeout=10))

if __name__ == '__main__':
    unittest.main()
