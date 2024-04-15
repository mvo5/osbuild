#!/usr/bin/python3

STAGE_NAME = "org.osbuild.groups"


def test_schema_supports_bootc_style_mounts(stage_schema, bootc_devices_mounts_dict):
    test_input = bootc_devices_mounts_dict
    test_input["type"] = STAGE_NAME
    res = stage_schema.validate(test_input)
    assert res.valid is True, f"err: {[e.as_dict() for e in res.errors]}"
