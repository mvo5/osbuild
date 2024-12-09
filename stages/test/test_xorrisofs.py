#!/usr/bin/python3

import os.path
import re
import subprocess
from unittest.mock import call, patch

import pytest

from osbuild import testutil
from osbuild.testutil import has_executable, make_fake_input_tree

STAGE_NAME = "org.osbuild.xorrisofs"


# XXX: move to testutils?
@pytest.fixture(name="fake_inputs")
def make_fake_inputs(tmp_path):
    fake_input_tree = make_fake_input_tree(tmp_path, {
        "/file1": "A file",
        "/file2": "Another file",
    })
    inputs = {
        "tree": {
            "path": fake_input_tree,
        }
    }
    return inputs


@pytest.mark.skipif(not has_executable("xorrisofs"), reason="no xorrisofs executable")
@patch("subprocess.run")
def test_syslinux_smoke(mocked_run, tmp_path, stage_module, fake_inputs):
    # taken from test/data/manifests/fedora-ostree-bootiso-xz.json
    options = {
        "filename": "fedora-ostree-boot.iso",
        "volid": "Fedora-41-X86_64",
        "boot": {
            "image": "isolinux/isolinux.bin",
            "catalog": "isolinux/boot.cat"
        },
        "efi": "images/efiboot.img",
        "isohybridmbr": "/usr/share/syslinux/isohdpfx.bin",
    }
    stage_module.main(fake_inputs, tmp_path / "tree", options)
    assert mocked_run.call_args_list == [
        call([
            "/usr/bin/xorrisofs", "-verbose",
            "-V", "Fedora-41-X86_64", "-isohybrid-mbr",
            "/usr/share/syslinux/isohdpfx.bin",
            "-b", "isolinux/isolinux.bin",
            "-c", "isolinux/boot.cat",
            "--boot-catalog-hide",
            "-boot-load-size", "4",
            "-boot-info-table",
            "-no-emul-boot",
            "-rock",
            "-joliet",
            "-eltorito-alt-boot",
            "-e", "images/efiboot.img",
            "-no-emul-boot",
            "-isohybrid-gpt-basdat",
            "-o", f"{tmp_path}/tree/fedora-ostree-boot.iso",
            f"{tmp_path}/tree",
        ], check=True)
    ]


@pytest.mark.skipif(not has_executable("xorrisofs"), reason="no xorrisofs executable")
@patch("subprocess.run")
def test_grub2_smoke(mocked_run, tmp_path, stage_module, fake_inputs):
    grub2_mbr_path = tmp_path / "grub2.mbr"
    grub2_mbr_path.write_text("")
    options = {
        # XXX: is this the correct value?
        "grub2": grub2_mbr_path.as_posix(),
        # XXX2: taken from test_syslinux_smoke, does this need adjustment?
        "filename": "fedora-ostree-boot.iso",
        "volid": "Fedora-41-X86_64",
        "boot": {
            "image": "isolinux/isolinux.bin",
            "catalog": "isolinux/boot.cat"
        },
        "efi": "images/efiboot.img",
    }
    stage_module.main(fake_inputs, tmp_path / "tree", options)
    expected_xorrisofs = call([
        "/usr/bin/xorrisofs",
        "-verbose",
        "-rock",
        "-joliet",
        "-V", "Fedora-41-X86_64",
        "--grub2-mbr", f"{tmp_path}/grub2.mbr",
        "-partition_offset", "16",
        "-appended_part_as_gpt",
        "-append_partition", "2", "C12A7328-F81F-11D2-BA4B-00A0C93EC93B",
        f"{tmp_path}/tree/images/efiboot.img",
        "-iso_mbr_part_type", "EBD0A0A2-B9E5-4433-87C0-68B6B72699C7",
        "-b", "isolinux/isolinux.bin",
        "-c", "isolinux/boot.cat",
        "--boot-catalog-hide",
        "-no-emul-boot",
        "-boot-load-size", "4",
        "-boot-info-table",
        "--grub2-boot-info",
        "-eltorito-alt-boot",
        "-e",
        "--interval:appended_partition_2:all::",
        "-no-emul-boot", 
        "-o", f"{tmp_path}/tree/fedora-ostree-boot.iso",
        f"{tmp_path}/tree",
    ], check=True)
    assert mocked_run.call_args_list == [expected_xorrisofs]

