import unittest
import os
import subprocess

class TestPartitionManager(unittest.TestCase):
    def test_script_exists(self):
        self.assertTrue(os.path.exists('src/partition_manager.sh'))

    def test_permissions(self):
        mode = oct(os.stat('src/partition_manager.sh').st_mode)[-3:]
        self.assertEqual(mode, '755')

    def test_logic_components(self):
        with open('src/partition_manager.sh', 'r') as f:
            content = f.read()
            self.assertIn('dd if=', content)
            self.assertIn('bs=1M', content)
            self.assertIn('sync', content)
            self.assertIn('/sdcard/GodTool_Backups/', content)

if __name__ == '__main__':
    unittest.main()
