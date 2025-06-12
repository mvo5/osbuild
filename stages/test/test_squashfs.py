#!/usr/bin/python3

import os.path
import subprocess
from unittest import mock

import pytest

from osbuild import testutil
from osbuild.testutil import has_executable, make_fake_input_tree

STAGE_NAME = "org.osbuild.squashfs"


@pytest.mark.skipif(not has_executable("mksquashfs"), reason="no mksquashfs")
@pytest.mark.parametrize("test_options,included,excluded", [
    ({}, ["subdir/file-in-subdir.txt\n", "file-in-root.txt\n"], []),
    ({"compression": {"method": "lz4"}}, ["subdir/file-in-subdir.txt\n", "file-in-root.txt\n"], []),
    ({"compression": {"method": "xz", "options": {"bcj": "x86"}}}, ["subdir/file-in-subdir.txt\n", "file-in-root.txt\n"], []),
    ({"exclude_paths": ["subdir/.*"]}, ["file-in-root.txt\n"], ["subdir/file-in-subdir.txt\n"]),
])
def test_squashfs_integration(tmp_path, stage_module, test_options, included, excluded):  # pylint: disable=unused-argument
    fake_input_tree = make_fake_input_tree(tmp_path, {
        "/file-in-root.txt": "other content",
        "/subdir/file-in-subdir.txt": "subdir content",
    })
    inputs = {
        "tree": {
            "path": fake_input_tree,
        }
    }
    filename = "some-file.img"
    options = {
        "filename": filename,
    }
    options.update(test_options)

    stage_module.main(inputs, tmp_path, options)

    img_path = os.path.join(tmp_path, "some-file.img")
    assert os.path.exists(img_path)
    # validate the content
    output = subprocess.check_output([
        "unsquashfs", "-ls", img_path], encoding="utf-8")
    for inc in included:
        assert inc in output
    for exc in excluded:
        assert not exc in output


@mock.patch("subprocess.run")
@pytest.mark.parametrize("test_options,expected", [
    ({}, []),
    ({"compression": {"method": "lz4"}}, ["-comp", "lz4"]),
    ({"compression": {"method": "xz", "options": {"bcj": "x86"}}}, ["-comp", "xz", "-Xbcj", "x86"]),
    ({"exclude_paths": ["boot/.*", "root/.*"]}, ["-regex", "-e", "boot/.*", "root/.*"])
])
def test_squashfs(mock_run, tmp_path, stage_module, test_options, expected):
    fake_input_tree = make_fake_input_tree(tmp_path, {})
    inputs = {
        "tree": {
            "path": fake_input_tree,
        }
    }
    filename = "some-file.img"
    options = {
        "filename": filename,
    }
    options.update(test_options)

    stage_module.main(inputs, tmp_path, options)

    expected = [
        "mksquashfs",
        f"{fake_input_tree}",
        f"{os.path.join(tmp_path, filename)}",
    ] + expected
    mock_run.assert_called_with(expected, check=True)


@pytest.mark.parametrize("test_data,expected_err", [
    # bad
    ({"extra": "option"}, "'extra' was unexpected"),
    ({"compression": {"method": "invalid"}}, "'invalid' is not one of ["),
    ({"compression": {}}, "'method' is a required property"),
    ({"compression": {"method": "xz", "options": {"bcj": "invalid"}}}, "'invalid' is not one of ["),
    ({"compression": {"method": "xz", "options": {"level": 9}}}, "Additional properties are not allowed"),
    # good
    ({"compression": {"method": "lz4"}}, ""),
    ({"exclude_paths": ["boot/", "root/"]}, "")
])
def test_schema_validation_squashfs(stage_schema, test_data, expected_err):
    test_input = {
        "type": STAGE_NAME,
        "options": {
            "filename": "some-filename.img",
        }
    }
    test_input["options"].update(test_data)
    res = stage_schema.validate(test_input)

    if expected_err == "":
        assert res.valid is True, f"err: {[e.as_dict() for e in res.errors]}"
    else:
        assert res.valid is False
        testutil.assert_jsonschema_error_contains(res, expected_err, expected_num_errs=1)
