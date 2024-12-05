#!/usr/bin/python3

import tempfile
import textwrap

import pytest

STAGE_NAME = "org.osbuild.coreos.live-artifacts.mono"


def test_get_os_features(tmp_path, stage_module):
    cfg_path = tmp_path / "usr/share/coreos-installer/example-config.yaml"
    cfg_path.parent.mkdir(parents=True)
    cfg_path.write_text(textwrap.dedent("""\
    # Fedora CoreOS stream
    stream: name
    # Manually specify the image URL
    image-url: URL
    """))
    features = stage_module.get_os_features(tmp_path)
    assert {
        "installer-config": True,
        "installer-config-directives": {
            "stream": True,
            "image-url": True,
        },
        "live-initrd-network": True,
    } == features
