#
# Tests for xdev installer GUI enhancements
# Distributed under the terms of the BSD 2-Clause License.
#

import os
import sys
import pytest
from unittest.mock import patch, MagicMock
import subprocess

# Ensure src is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))


class DummyWizard:
    """Mock wizard instance for testing installer logic."""
    def __init__(self):
        import queue
        self.ui_queue = queue.Queue()
        self.repo_path = MagicMock()
        self.repo_path.get.return_value = r"D:\XenevaOS"

    # Bind the methods from xdev_installer_gui
    from xdev_installer_gui import XdevSetupWizard
    check_c_drive_space = XdevSetupWizard.check_c_drive_space
    execute_command = XdevSetupWizard.execute_command
    init_pacman_keys_and_sync = XdevSetupWizard.init_pacman_keys_and_sync


def test_disk_space_check_sufficient():
    wizard = DummyWizard()
    # Mock disk_usage returning 10 GB free space
    fake_usage = (50 * 1024**3, 40 * 1024**3, 10 * 1024**3)
    with patch("shutil.disk_usage", return_value=fake_usage):
        passed, free_gb = wizard.check_c_drive_space(min_gb=5.0)
        assert passed is True
        assert free_gb == pytest.approx(10.0, 0.1)


def test_disk_space_check_insufficient():
    wizard = DummyWizard()
    # Mock disk_usage returning 3 GB free space
    fake_usage = (50 * 1024**3, 47 * 1024**3, 3 * 1024**3)
    with patch("shutil.disk_usage", return_value=fake_usage):
        passed, free_gb = wizard.check_c_drive_space(min_gb=5.0)
        assert passed is False
        assert free_gb == pytest.approx(3.0, 0.1)


def test_pacman_sync_handles_network_timeout():
    wizard = DummyWizard()
    
    # Mock execute_command to raise TimeoutExpired on sync
    call_count = 0
    def fake_execute(cmd_str, status_msg, stream=True, allowed_exit_codes=None, timeout=None):
        nonlocal call_count
        call_count += 1
        if "pacman -Sy" in cmd_str:
            raise subprocess.TimeoutExpired(cmd_str, timeout or 120)
        return

    wizard.execute_command = fake_execute

    with patch("time.sleep"):  # Speed up retry delay
        # Should complete gracefully without raising uncaught exception
        wizard.init_pacman_keys_and_sync(max_retries=2, timeout_seconds=5)

    # Check that UI logs recorded the network timeout
    messages = []
    while not wizard.ui_queue.empty():
        messages.append(wizard.ui_queue.get())

    log_texts = [m[2] for m in messages if m[0] == "LOG" and m[2] is not None]
    assert any("Network timeout" in t for t in log_texts)
    assert any("All repository sync attempts timed out" in t for t in log_texts)


def test_execute_command_timeout():
    wizard = DummyWizard()
    # Test execute_command streaming mode timeout
    with pytest.raises(subprocess.TimeoutExpired):
        wizard.execute_command("powershell -Command Start-Sleep -Seconds 10", "Sleeping", stream=True, timeout=1)
