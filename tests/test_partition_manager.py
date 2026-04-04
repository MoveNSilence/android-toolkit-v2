import unittest
import os

class TestPartitionManager(unittest.TestCase):
    def setUp(self):
        self.script_path = 'src/partition_manager.sh'

    def test_script_exists(self):
        self.assertTrue(os.path.exists(self.script_path))

    def test_script_is_executable(self):
        self.assertTrue(os.access(self.script_path, os.X_OK))

    def test_script_logic_content(self):
        with open(self.script_path, 'r') as f:
            content = f.read()

        # Verify key logic components as requested
        self.assertIn('prism|modemst1|modemst2', content)
        self.assertIn('readlink -f "/dev/block/by-name/$PARTITION"', content)
        self.assertIn('BACKUP_DIR="/sdcard/GodTool_Backups"', content)
        self.assertIn('dd if="$BLOCK_DEV" of="$BACKUP_FILE" bs=4096 conv=notrunc', content)
        self.assertIn('dd if="$IMAGE_PATH" of="$BLOCK_DEV" bs=4096 conv=notrunc', content)
        self.assertIn('sync', content)

if __name__ == '__main__':
    unittest.main()
