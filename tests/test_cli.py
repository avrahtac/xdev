#
# Tests for xdev CLI toolchain
# Distributed under the terms of the BSD 2-Clause License.
#

import os
import sys
import pytest
from unittest.mock import patch, MagicMock
import subprocess

# Ensure src is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))
import xdev_cli


class TestCommandLineArgParsing:
    """Tests for command-line argument parsing and subcommand dispatch."""

    def test_help_command(self, capsys):
        for arg in ["help", "--help", "-h"]:
            with pytest.raises(SystemExit) as excinfo:
                xdev_cli.main([arg])
            assert excinfo.value.code == 0
            captured = capsys.readouterr()
            assert "usage: xdev <command>" in captured.out
            assert "doctor" in captured.out
            assert "build" in captured.out
            assert "run" in captured.out

    def test_no_arguments_shows_help(self, capsys):
        with pytest.raises(SystemExit) as excinfo:
            xdev_cli.main([])
        assert excinfo.value.code == 0
        captured = capsys.readouterr()
        assert "usage: xdev <command>" in captured.out

    def test_unknown_command_exits_with_error(self, capsys):
        with pytest.raises(SystemExit) as excinfo:
            xdev_cli.main(["nonexistent_command"])
        assert excinfo.value.code == 1
        captured = capsys.readouterr()
        assert "xdev: error: unknown command 'nonexistent_command'" in captured.err
        assert "see 'xdev help'" in captured.err

    def test_build_forwards_extra_arguments(self, tmp_path, monkeypatch):
        monkeypatch.setenv("XENEVA_PROJECT", str(tmp_path))
        with patch("shutil.which", return_value="make"), \
             patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            with pytest.raises(SystemExit) as excinfo:
                xdev_cli.main(["build", "clean", "llvm", "VERBOSE=1"])
            assert excinfo.value.code == 0
            mock_run.assert_called_once()
            cmd_called = mock_run.call_args[0][0]
            assert cmd_called[1:] == ["clean", "llvm", "VERBOSE=1"]
            assert mock_run.call_args[1]["cwd"] == str(tmp_path)

    def test_run_forwards_extra_arguments(self, tmp_path, monkeypatch):
        monkeypatch.setenv("XENEVA_PROJECT", str(tmp_path))
        fat_img = tmp_path / "fat.img"
        fat_img.write_text("dummy")
        with patch("xdev_cli.find_qemu_binary", return_value=("qemu-system-x86_64", "qemu-system-x86_64")), \
             patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            with pytest.raises(SystemExit) as excinfo:
                xdev_cli.main(["run", "-display", "none", "-no-reboot"])
            assert excinfo.value.code == 0
            mock_run.assert_called_once()
            cmd_called = mock_run.call_args[0][0]
            assert "-display" in cmd_called
            assert "none" in cmd_called
            assert "-no-reboot" in cmd_called

    def test_flash_requires_target_argument(self, capsys):
        with pytest.raises(SystemExit) as excinfo:
            xdev_cli.main(["flash"])
        assert excinfo.value.code == 1
        captured = capsys.readouterr()
        assert "xdev: error: target storage device/drive required" in captured.err


class TestEnvironmentVariableDetection:
    """Tests for detection and validation of the XENEVA_PROJECT environment variable."""

    def test_xeneva_project_not_set_doctor(self, monkeypatch, capsys):
        monkeypatch.delenv("XENEVA_PROJECT", raising=False)
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="v1.0")
            code = xdev_cli.run_doctor()
            assert code == 1
            captured = capsys.readouterr()
            assert "XENEVA_PROJECT: not set" in captured.out

    def test_xeneva_project_invalid_directory_doctor(self, monkeypatch, capsys):
        monkeypatch.setenv("XENEVA_PROJECT", r"Z:\nonexistent_xeneva_dir_12345")
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="v1.0")
            code = xdev_cli.run_doctor()
            assert code == 1
            captured = capsys.readouterr()
            assert "not a valid directory" in captured.out

    def test_xeneva_project_valid_directory_doctor(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setenv("XENEVA_PROJECT", str(tmp_path))
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="v1.0")
            code = xdev_cli.run_doctor()
            assert code == 0
            captured = capsys.readouterr()
            assert f"XENEVA_PROJECT: {tmp_path}" in captured.out

    def test_xeneva_project_not_set_build(self, monkeypatch, capsys):
        monkeypatch.delenv("XENEVA_PROJECT", raising=False)
        with pytest.raises(SystemExit) as excinfo:
            xdev_cli.main(["build"])
        assert excinfo.value.code == 1
        captured = capsys.readouterr()
        assert "xdev: error: XENEVA_PROJECT environment variable is not set" in captured.err

    def test_xeneva_project_invalid_path_build(self, monkeypatch, capsys):
        monkeypatch.setenv("XENEVA_PROJECT", r"Z:\invalid\repo\path")
        with pytest.raises(SystemExit) as excinfo:
            xdev_cli.main(["build"])
        assert excinfo.value.code == 1
        captured = capsys.readouterr()
        assert "xdev: error: XENEVA_PROJECT directory not found" in captured.err

    def test_build_invokes_make_inside_xeneva_project(self, tmp_path, monkeypatch):
        monkeypatch.setenv("XENEVA_PROJECT", str(tmp_path))
        with patch("shutil.which", return_value="make"), \
             patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            with pytest.raises(SystemExit) as excinfo:
                xdev_cli.main(["build"])
            assert excinfo.value.code == 0
            assert mock_run.call_args[1]["cwd"] == str(tmp_path)

    def test_xeneva_project_not_set_run(self, monkeypatch, capsys):
        monkeypatch.delenv("XENEVA_PROJECT", raising=False)
        with pytest.raises(SystemExit) as excinfo:
            xdev_cli.main(["run"])
        assert excinfo.value.code == 1
        captured = capsys.readouterr()
        assert "xdev: error: XENEVA_PROJECT environment variable is not set" in captured.err

    def test_xeneva_project_no_image_run(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setenv("XENEVA_PROJECT", str(tmp_path))
        with pytest.raises(SystemExit) as excinfo:
            xdev_cli.main(["run"])
        assert excinfo.value.code == 1
        captured = capsys.readouterr()
        assert "xdev: error: compiled OS image (fat.img) not found in XENEVA_PROJECT" in captured.err

    def test_run_launches_qemu_inside_xeneva_project(self, tmp_path, monkeypatch):
        monkeypatch.setenv("XENEVA_PROJECT", str(tmp_path))
        fat_img = tmp_path / "fat.img"
        fat_img.write_text("dummy image")
        with patch("xdev_cli.find_qemu_binary", return_value=("qemu-system-x86_64", "qemu-system-x86_64")), \
             patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            with pytest.raises(SystemExit) as excinfo:
                xdev_cli.main(["run"])
            assert excinfo.value.code == 0
            assert mock_run.call_args[1]["cwd"] == str(tmp_path)
            cmd_called = mock_run.call_args[0][0]
            assert any(str(fat_img) in arg for arg in cmd_called)


class TestDoctorDependenciesAndExitCodes:
    """Tests for xdev doctor dependency checking, error handling, and exit codes."""

    def test_doctor_all_dependencies_present(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setenv("XENEVA_PROJECT", str(tmp_path))
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="tool version 1.0.0")
            code = xdev_cli.run_doctor()
            assert code == 0
            captured = capsys.readouterr()
            assert "missing" not in captured.out
            assert "found git" in captured.out
            assert "found clang" in captured.out
            assert "found lld" in captured.out
            assert "found qemu-system-aarch64" in captured.out
            assert "found make" in captured.out
            assert "found mtools" in captured.out

    @pytest.mark.parametrize("missing_tool", ["git", "clang", "lld", "qemu-system-aarch64", "make", "mtools"])
    def test_doctor_single_missing_dependency_exit_code(self, tmp_path, monkeypatch, missing_tool, capsys):
        monkeypatch.setenv("XENEVA_PROJECT", str(tmp_path))

        def fake_run(cmd, *args, **kwargs):
            first_cmd = cmd[0].lower()
            target_match = "mcopy" if missing_tool == "mtools" else missing_tool
            if target_match in first_cmd:
                return MagicMock(returncode=1, stdout="", stderr="not found")
            return MagicMock(returncode=0, stdout=f"{first_cmd} v1.0", stderr="")

        with patch("subprocess.run", side_effect=fake_run):
            code = xdev_cli.run_doctor()
            assert code == 1
            captured = capsys.readouterr()
            assert f"missing {missing_tool}" in captured.out

    def test_doctor_file_not_found_dependency_exit_code(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setenv("XENEVA_PROJECT", str(tmp_path))

        def fake_run(cmd, *args, **kwargs):
            if "clang" in cmd[0]:
                raise FileNotFoundError("clang not found")
            return MagicMock(returncode=0, stdout="ok")

        with patch("subprocess.run", side_effect=fake_run):
            code = xdev_cli.run_doctor()
            assert code == 1
            captured = capsys.readouterr()
            assert "missing clang" in captured.out

    def test_doctor_preserves_existing_binary_paths(self):
        """Verify that existing binary paths in xdev_cli.py have not been altered."""
        import inspect
        source = inspect.getsource(xdev_cli.run_doctor)
        assert r'C:\msys64\ucrt64\bin\clang.exe' in source
        assert r'C:\msys64\ucrt64\bin\ld.lld.exe' in source
        assert r'C:\msys64\ucrt64\bin\qemu-system-aarch64.exe' in source
        assert r'C:\msys64\usr\bin\make.exe' in source
        assert r'C:\msys64\ucrt64\bin\mcopy.exe' in source


class TestSubprocessIntegration:
    """End-to-end tests invoking the CLI as a separate process."""

    def test_e2e_help_flag(self):
        res = subprocess.run([sys.executable, "src/xdev_cli.py", "--help"], capture_output=True, text=True)
        assert res.returncode == 0
        assert "usage: xdev <command>" in res.stdout

    def test_e2e_unknown_command(self):
        res = subprocess.run([sys.executable, "src/xdev_cli.py", "invalid_cmd"], capture_output=True, text=True)
        assert res.returncode == 1
        assert "xdev: error: unknown command" in res.stderr

    def test_e2e_doctor_runs(self):
        res = subprocess.run([sys.executable, "src/xdev_cli.py", "doctor"], capture_output=True, text=True)
        # Doctor prints XENEVA_PROJECT and dependencies
        assert "XENEVA_PROJECT:" in res.stdout
        assert "found" in res.stdout or "missing" in res.stdout

