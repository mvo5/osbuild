#!/usr/bin/python3

import os.path
import pathlib
import subprocess
import sys

import pytest

import osbuild.meta
from osbuild.testutil import has_executable
from osbuild.testutil.imports import import_module_from_path

TEST_INPUT = [
    ({
        "specifications": [
            {
                "user": "user1",
                "host": "ALL",
                "target": "ALL",
                "command": "ALL",
            },
        ],
    }, "user1 ALL = (ALL) ALL"),
]


@pytest.fixture(name="tmp_path_with_sudoers_d")
def tmp_path_with_sudoers_d_fixture(tmp_path):
    tmp_path_with_sudoers_d = os.fspath(pathlib.Path(f"{tmp_path}/etc/sudoers.d"))
    os.makedirs(tmp_path_with_sudoers_d)
    return tmp_path


# XXX: extremly similar to the kickstart test, consolidate in testutil
def schema_validate_sudo_stage(test_data):
    name = "org.osbuild.sudoers"
    root = os.path.join(os.path.dirname(__file__), "../..")
    mod_info = osbuild.meta.ModuleInfo.load(root, "Stage", name)
    schema = osbuild.meta.Schema(mod_info.get_schema(), name)
    test_input = {
        "name": "org.osbuild.sudoers",
        "options": {
            "filename": "10-test",
        }
    }
    test_input["options"].update(test_data)
    return schema.validate(test_input)


@pytest.mark.parametrize("test_input,expected", TEST_INPUT)
def test_sudoers_test_cases_valid(test_input, expected):  # pylint: disable=unused-argument
    """ ensure all test inputs are valid """
    res = schema_validate_sudo_stage(test_input)
    assert res.valid is True, f"input: {test_input}\nerr: {[e.as_dict() for e in res.errors]}"


def _run_sudoers_stage(tmp_path, test_input):
    stage_path = os.path.join(os.path.dirname(__file__), "../org.osbuild.sudoers")
    stage = import_module_from_path("stage", stage_path)

    filename = "20-test"
    options = {"filename": filename}
    options.update(test_input)

    stage.main(tmp_path, options)

    return pathlib.Path(f"{tmp_path}/etc/sudoers.d/{filename}")


@pytest.mark.parametrize("test_input,expected", TEST_INPUT)
def test_sudoers_write(tmp_path_with_sudoers_d, test_input, expected):
    cfg_path = _run_sudoers_stage(tmp_path_with_sudoers_d, test_input)

    with open(cfg_path, encoding="utf-8") as fp:
        cfg_content = fp.read()
    assert cfg_content == expected + "\n"


@pytest.mark.skipif(not has_executable("visudo"), reason="`visudo` is required")
@pytest.mark.parametrize("test_input,expected", TEST_INPUT)
def test_sudoers_valid(tmp_path_with_sudoers_d, test_input, expected):  # pylint: disable=unused-argument
    cfg_path = _run_sudoers_stage(tmp_path_with_sudoers_d, test_input)

    # check with visudo if the file looks valid
    subprocess.check_call(["visudo", "-cf", cfg_path], stdout=sys.stdout, stderr=sys.stderr)


@pytest.mark.parametrize(
    "test_data,expected_err",
    [
        ({"specifications": "invalid"}, " is not of type 'array'"),
        ({"specifications": ["invalid"]}, " is not of type 'object'"),
        ({"specifications": [{"user":"invalid;user"}]}, " does not match "),
    ],
)
def test_sudoers_schema_validation_bad(test_data, expected_err):
    res = schema_validate_sudo_stage(test_data)

    assert res.valid is False
    assert len(res.errors) == 1
    err_msgs = [e.as_dict()["message"] for e in res.errors]
    assert expected_err in err_msgs[0]
