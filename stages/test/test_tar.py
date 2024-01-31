#!/usr/bin/python3

import os.path
import tarfile

import pytest

from osbuild.testutil.imports import import_module_from_path

STAGE_NAME = "org.osbuild.tar"


# TODO: once rebase to main use osbuild.testutil.make_fake_input_tree
def make_fake_input_tree(tmpdir, fake_content: dict) -> str:
    basedir = os.path.join(tmpdir, "tree")
    for path, content in fake_content.items():
        dirp, name = os.path.split(os.path.join(basedir, path.lstrip("/")))
        os.makedirs(dirp, exist_ok=True)
        with open(os.path.join(dirp, name), "w", encoding="utf-8") as fp:
            fp.write(content)
    return basedir


TEST_INPUT = [
    ({}, [".", "./root.txt", "./subdir", "./subdir/subdir.txt"]),
    ({"paths": ["./subdir"]}, ["./subdir", "./subdir/subdir.txt"]),
]


@pytest.mark.parametrize("test_options,expected_content", TEST_INPUT)
def test_tar_integration(tmp_path, test_options, expected_content):
    # TODO: once rebased to master use the "stage_module" fixture
    stage_path = os.path.join(os.path.dirname(__file__), f"../{STAGE_NAME}")
    stage = import_module_from_path("erofs_stage", stage_path)

    fake_input_tree = make_fake_input_tree(tmp_path, {
        "/root.txt": "root content",
        "/subdir/subdir.txt": "subdir content",
    })
    inputs = {
        "tree": {
            "path": fake_input_tree,
        }
    }
    filename = "some-file.tar"
    options = {
        "filename": filename,
    }
    options.update(test_options)

    stage.main(inputs, tmp_path, options)

    tar_path = os.path.join(tmp_path, "some-file.tar")
    assert os.path.exists(tar_path)
    # validate the content
    tf = tarfile.open(tar_path)
    assert sorted(tf.getnames()) == sorted(expected_content)
