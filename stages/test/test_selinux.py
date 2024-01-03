#!/usr/bin/python3

import os.path
from unittest.mock import call, patch

import pytest

import osbuild.meta
from osbuild.testutil.imports import import_module_from_path


def schema_validation_selinux(test_data):
    name = "org.osbuild.selinux"
    root = os.path.join(os.path.dirname(__file__), "../..")
    mod_info = osbuild.meta.ModuleInfo.load(root, "Stage", name)
    schema = osbuild.meta.Schema(mod_info.get_schema(version="1"), name)

    test_input = {
        "name": "org.osbuild.selinux",
        "options": {},
    }
    test_input["options"].update(test_data)
    return schema.validate(test_input)


@pytest.mark.parametrize("test_data,expected_err", [
    # good
    ({}, ""),
    ({"file_contexts": "etc/selinux/targeted/contexts/files/file_contexts"}, ""),
    ({"labels": {"/usr/bin/cp": "system_u:object_r:install_exec_t:s0"}}, ""),
    ({"force_autorelabel": True}, ""),
    # bad
    ({"file_contexts": 1234}, "1234 is not of type 'string'"),
    ({"labels": "xxx"}, "'xxx' is not of type 'object'"),
    ({"force_autorelabel": "foo"}, "'foo' is not of type 'boolean'"),
])
def test_schema_validation_selinux(test_data, expected_err):
    res = schema_validation_selinux(test_data)
    if expected_err == "":
        assert res.valid is True, f"err: {[e.as_dict() for e in res.errors]}"
    else:
        assert res.valid is False
        assert len(res.errors) == 1, [e.as_dict() for e in res.errors]
        err_msgs = [e.as_dict()["message"] for e in res.errors]
        assert expected_err in err_msgs[0]

@pytest.mark.parametrize("test_data,expected_selinux_spec", [
    ({}, ""),
    ({"file_contexts": "/etc/selinux/path"}, "/etc/selinux/path"),
])
@patch("subprocess.run")
def test_selinux_file_contexts(mocked_run, tmp_path, test_data, expected_selinux_spec):
    stage_path = os.path.join(os.path.dirname(__file__), "../org.osbuild.selinux")
    stage = import_module_from_path("stage", stage_path)

    options = {}
    options.update(test_data)
    stage.main(tmp_path, options)

    if expected_selinux_spec:
        assert len(mocked_run.call_args_list) == 1
        assert mocked_run.call_args_list == [
            call(
                ["setfiles", "-F", "-r", os.fspath(tmp_path),
                 expected_selinux_spec, os.fspath(tmp_path)], check=True),
        ]
    else:
        assert mocked_run.call_args_list == []
