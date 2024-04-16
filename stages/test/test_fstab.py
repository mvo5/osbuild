#!/usr/bin/python3

import pytest

from osbuild.testutil import assert_jsonschema_error_contains

STAGE_NAME = "org.osbuild.fstab"


@pytest.mark.parametrize("test_data,expected_err", [
    # bad
    ({}, "'filesystems' is a required property"),
    ({"filesystems": [{"missing": "properties"}]}, " is not valid under any of the given schemas"),
    # good
    ({"filesystems": []}, ""),
    ({"filesystems": [{"path": "/some/path", "uuid": "some-uuid"}]}, ""),
])
def test_schema_validation(stage_schema, test_data, expected_err):
    test_input = {
        "type": STAGE_NAME,
        "options": {},
    }
    test_input["options"].update(test_data)
    res = stage_schema.validate(test_input)

    if expected_err == "":
        assert res.valid is True, f"err: {[e.as_dict() for e in res.errors]}"
    else:
        assert res.valid is False
        assert_jsonschema_error_contains(res, expected_err, expected_num_errs=1)


def test_schema_supports_bootc_style_mounts(stage_schema, bootc_devices_mounts_dict):
    test_input = bootc_devices_mounts_dict
    test_input["type"] = STAGE_NAME
    res = stage_schema.validate(test_input)
    assert res.valid is True, f"err: {[e.as_dict() for e in res.errors]}"
