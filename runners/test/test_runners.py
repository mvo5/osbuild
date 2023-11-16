#!/usr/bin/python3

import os
import pathlib
import subprocess
import sys
from unittest.mock import patch, call

import pytest

from osbuild.testutil.imports import import_module_from_path


runner_dir = pathlib.Path(__file__).parent.parent

FEDORA_LIKE_SETUP = [
    call(["touch", "/etc/ld.so.conf"], check=True),
    call(["ldconfig"], check=True),
    call(["systemd-sysusers"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True),
    call(["systemd-tmpfiles", "--create"], check=False),
]

TEST_INPUT = [
    ("centos9", FEDORA_LIKE_SETUP, [call("/etc/nsswitch.conf")]),
    ("fedora30", FEDORA_LIKE_SETUP, [call("/etc/nsswitch.conf")]),
    ("linux", [], []),
]


@pytest.mark.parametrize("runner,expected_calls,expected_removes", TEST_INPUT)
@patch("sys.exit")
@patch("subprocess.run")
@patch("os.remove")
@patch("osbuild.api.exception_handler")
def test_runners_linux(mock_ex, mock_os_remove, mock_run, mock_sys_exit, tmp_path, runner, expected_calls, expected_removes):
    fake_sys_argv = ["argv0", "random-cmd", "with", "args"]
    sys.argv = fake_sys_argv
    mock_run.return_value = subprocess.CompletedProcess(fake_sys_argv, 0)

    # import as __main__ to run the runner
    runner = pathlib.Path(f"{runner_dir}/org.osbuild.{runner}")
    mod = import_module_from_path("__main__", os.fspath(runner))
    # checks
    mock_sys_exit.assert_called_once_with(0)

    main_call = [call(fake_sys_argv[1:], check=False)]
    expected_calls = expected_calls + main_call
    mock_run.assert_has_calls(expected_calls)
    mock_os_remove.assert_has_calls(expected_removes)

