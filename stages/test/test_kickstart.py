#!/usr/bin/python3

import os.path
import shutil
import unittest
from tempfile import mkdtemp

from org_osbuild_kickstart import main as kickstart_main

test_cases = [
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
    {
        "options": {"zerombr": "true"},
        "expected": "zerombr",
    },
    {
        "options": {"clearpart": {}},
        "expected": "clearpart",
    },
    {
        "options": {"clearpart": {"all": True}},
        "expected": "clearpart --all",
    },
    {
        "options": {"clearpart": {"drives": ["hda","hdb"]}},
        "expected": "clearpart --drives=hda,hdb",
    },
    {
        "options": {"clearpart": {"drives": ["hda"]}},
        "expected": "clearpart --drives=hda",
    },
    {
        "options": {"clearpart": {"list": ["sda2","sda3"]}},
        "expected": "clearpart --list=sda2,sda3",
    },
    {
        "options": {"clearpart": {"list": ["sda2"]}},
        "expected": "clearpart --list=sda2",
    },
    {
        "options": {"clearpart": {"disklabel": "some-label"}},
        "expected": "clearpart --disklabel=some-label",
    },
    {
        "options": {"clearpart": {"linux": True}},
        "expected": "clearpart --linux",
    },
    {
        "options": {
            "clearpart": {
                "all": True,
                "drives": ["hda", "hdb"],
                "list": ["sda2","sda3"],
                "disklabel": "some-label",
                "linux": True,
            }
        },
        "expected": "clearpart --all --drives=hda,hdb --list=sda2,sda3 --disklabel=some-label --linux",
    },

]


class TestOrgOsbuilderKickstart(unittest.TestCase):

    def setUp(self):
        self.tmpdir = mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmpdir)

    def test_kickstart(self):
        ks_path = "kickstart/kfs.cfg"
        for tc in test_cases:
            options = {"path": ks_path}
            options.update(tc["options"])
            kickstart_main(self.tmpdir, options)

            with open(os.path.join(self.tmpdir, ks_path), encoding="utf-8") as fp:
                ks_content = fp.read()
            self.assertEqual(ks_content, tc["expected"] + "\n")


if __name__ == "__main__":
    unittest.main()
