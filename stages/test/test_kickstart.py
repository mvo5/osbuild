#!/usr/bin/python3

import os.path
import tempfile

import pytest
from org_osbuild_kickstart import main as kickstart_main


@pytest.fixture(name="ks_test_cases")
def ks_test_cases_fixtures():
    return [
        {
            "options": {"lang": "en_US.UTF-8"},
            "expected": "lang en_US.UTF-8",
        },
        {
            "options": {"keyboard": "us"},
            "expected": "keyboard us",
        },
        {
            "options": {"timezone": "UTC"},
            "expected": "timezone UTC",
        },
        {
            "options": {
                "lang": "en_US.UTF-8",
                "keyboard": "us",
                "timezone": "UTC",
            },
            "expected": "lang en_US.UTF-8\nkeyboard us\ntimezone UTC",
        },
    ]


def test_kickstart(ks_test_cases):
    ks_path = "kickstart/kfs.cfg"
    with tempfile.TemporaryDirectory("kickstart-test-") as tmpdir:
        for tc in ks_test_cases:
            options = {"path": ks_path}
            options.update(tc["options"])
            kickstart_main(tmpdir, options)

            with open(os.path.join(tmpdir, ks_path), encoding="utf-8") as fp:
                ks_content = fp.read()
            assert ks_content == tc["expected"] + "\n"
