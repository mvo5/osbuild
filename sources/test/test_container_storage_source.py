#!/usr/bin/python3

import random
import pathlib
import socket
import string
import subprocess
import textwrap
from unittest.mock import patch

import pytest

from osbuild.testutil import has_executable, make_container, make_fake_tree

SOURCES_NAME = "org.osbuild.containers-storage"


@pytest.mark.skipif(not has_executable("podman"), reason="no podman executable")
def test_containers_storage_integration(tmp_path, sources_module):
    base_tag = "container-" + "".join(random.choices(string.digits, k=12))
    make_container(tmp_path, base_tag, {
        "file1": "file1 content",
    })
    image_id = subprocess.check_output(
        ["podman", "inspect", "-f", "{{ .Id }}", base_tag]).strip()
    digest = subprocess.check_output(
        ["podman", "inspect", "-f", "{{ .Digest }}", base_tag]).strip()
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    cnt_storage = sources_module.ContainersStorageSource.from_args(["--service-fd", str(sock.fileno())])
    desc = {
        "image": {
            "name": "some-name",
            "digest": digest,
        },
    }
    assert cnt_storage.exists(image_id, desc) == True
