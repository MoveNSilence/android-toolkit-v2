import pytest
import src.modem as modem
import re

def test_flash_partition_security():
    # Valid partition name
    try:
        # We expect FileNotFoundError because local_image_path likely doesn't exist
        # But partition_name validation happens first.
        # So if we pass a valid partition name but invalid file path, it should fail with FileNotFoundError
        # If we pass an invalid partition name, it should fail with ValueError

        modem.flash_partition("127.0.0.1", "modemst1", "nonexistent.img")
    except FileNotFoundError:
        pass
    except ValueError:
        pytest.fail("Valid partition name should not raise ValueError")

    # Invalid partition name
    with pytest.raises(ValueError, match="Invalid partition name"):
        modem.flash_partition("127.0.0.1", "modem;reboot", "nonexistent.img")
