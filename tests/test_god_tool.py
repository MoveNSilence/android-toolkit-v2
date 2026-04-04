import sys
import os
import unittest
from unittest.mock import patch, MagicMock

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.god_tool import analyze_partitions, main, DEFAULT_TARGET_IP

class TestGodTool(unittest.TestCase):

    @patch('src.god_tool.subprocess.run')
    def test_analyze_partitions_success(self, mock_run):
        # Should not raise any exception
        analyze_partitions()
        mock_run.assert_called_once_with(["adb", "shell", "ls -l /dev/block/by-name/"], check=True)

    @patch('src.god_tool.subprocess.run')
    def test_analyze_partitions_failure(self, mock_run):
        import subprocess
        mock_run.side_effect = subprocess.CalledProcessError(1, 'adb')
        # Should catch the error and print a message
        analyze_partitions()
        mock_run.assert_called_once()

    @patch('src.god_tool.connect_to_device')
    @patch('src.god_tool.analyze_partitions')
    @patch('sys.argv', ['god_tool.py'])
    def test_main_success(self, mock_analyze, mock_connect):
        mock_connect.return_value = True
        main()
        mock_connect.assert_called_once_with(DEFAULT_TARGET_IP)
        mock_analyze.assert_called_once()

    @patch('src.god_tool.connect_to_device')
    @patch('src.god_tool.analyze_partitions')
    @patch('sys.exit')
    @patch('sys.argv', ['god_tool.py'])
    def test_main_failure(self, mock_exit, mock_analyze, mock_connect):
        mock_connect.return_value = False
        main()
        mock_connect.assert_called_once_with(DEFAULT_TARGET_IP)
        mock_analyze.assert_not_called()
        mock_exit.assert_called_once_with(1)

    @patch('src.god_tool.connect_to_device')
    @patch('src.god_tool.analyze_partitions')
    @patch('sys.argv', ['god_tool.py', '--target', '1.2.3.4:5555'])
    def test_main_custom_target(self, mock_analyze, mock_connect):
        mock_connect.return_value = True
        main()
        mock_connect.assert_called_once_with('1.2.3.4:5555')
        mock_analyze.assert_called_once()

if __name__ == '__main__':
    unittest.main()
