#!/usr/bin/python3

import pathlib
import socket
import subprocess
import textwrap
from unittest.mock import patch

import pytest

from osbuild.util.checksum import verify_file

SOURCES_NAME = "org.osbuild.curl"

TEST_SOURCE_PAIRS = [
    (
        # sha256("0")
        "sha256:5feceb66ffc86f38d952786c6d696c79c2dbc239dd4e91b46729d73a27fb57e9",
        {
            "url": "http://example.com/file/0",
        },
    ), (
        # sha256("1")
        "sha256:6b86b273ff34fce19d6b804eff5a3f5747ada4eaa22f1d49c01e52ddb7875b4b",
        {
            "url": "http://example.com/file/1",
            "insecure": True,
        },
    ), (
        # sha256("2")
        "sha256:d4735e3a265e16eee03f59718b9b5d03019c07d8b6c51f90da3a666eec13ab35",
        {
            "url": "http://example.com/file/2",
            "secrets": {
                "ssl_ca_cert": "some-ssl_ca_cert",
            },
        },
    ), (
        # sha256("3")
        "sha256:4e07408562bedb8b60ce05c1decfe3ad16b72230967de01f640b7e4729b49fce",
        {
            "url": "http://example.com/file/3",
            "secrets": {
                "ssl_client_cert": "some-ssl_client_cert",
                "ssl_client_key": "some-ssl_client_key",
            },
        },
    ),
]


def test_curl_gen_download_config(tmp_path, sources_module):
    config_path = tmp_path / "curl-config.txt"
    # pylint: disable=W0212
    sources_module._gen_curl_download_config(TEST_SOURCE_PAIRS, config_path)
    assert config_path.exists()
    assert config_path.read_text(encoding="utf8") == textwrap.dedent("""\
    url = "http://example.com/file/0"
    output = "sha256:5feceb66ffc86f38d952786c6d696c79c2dbc239dd4e91b46729d73a27fb57e9"
    no-insecure

    url = "http://example.com/file/1"
    output = "sha256:6b86b273ff34fce19d6b804eff5a3f5747ada4eaa22f1d49c01e52ddb7875b4b"
    insecure

    url = "http://example.com/file/2"
    output = "sha256:d4735e3a265e16eee03f59718b9b5d03019c07d8b6c51f90da3a666eec13ab35"
    cacert = "some-ssl_ca_cert"
    no-insecure

    url = "http://example.com/file/3"
    output = "sha256:4e07408562bedb8b60ce05c1decfe3ad16b72230967de01f640b7e4729b49fce"
    cert = "some-ssl_client_cert"
    key = "some-ssl_client_key"
    no-insecure

    """)


def test_split_chsum_desc_tuples(sources_module):
    # pylint: disable=W0212
    split = sources_module._split_chksum_desc_tuples(TEST_SOURCE_PAIRS, 2)
    assert len(split) == len(TEST_SOURCE_PAIRS) // 2
    for itms in split:
        assert len(itms) == 2

    # pylint: disable=W0212
    split = sources_module._split_chksum_desc_tuples(TEST_SOURCE_PAIRS, 99)
    assert len(split) == len(TEST_SOURCE_PAIRS)
    for itms in split:
        assert len(itms) == 1


@patch("subprocess.run")
def test_curl_download_many_fail(patched_run, tmp_path, sources_module):
    fake_completed_process = subprocess.CompletedProcess(["args"], 91)
    fake_completed_process.stderr = "something bad happend"

    patched_run.return_value = fake_completed_process
    # source will automatically close the socket on __del__()
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    curl = sources_module.CurlSource.from_args(["--service-fd", str(sock.fileno())])
    curl.cache = tmp_path / "curl-cache"
    curl.cache.mkdir(parents=True, exist_ok=True)

    with pytest.raises(RuntimeError) as exp:
        curl.fetch_many(TEST_SOURCE_PAIRS)
    assert str(exp.value) == 'curl error: "something bad happend": error code 91'


@patch("subprocess.run")
def test_curl_download_many(mocked_run, tmp_path, sources_module):
    def _fake_download(*args, **kwargs):
        download_dir = pathlib.Path(kwargs["cwd"])
        for chksum, desc in TEST_SOURCE_PAIRS:
            (download_dir / chksum).write_text(desc["url"][-1], encoding="utf8")
        return subprocess.CompletedProcess(args, 0)
    mocked_run.side_effect = _fake_download
    # source will automatically close the socket on __del__()
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    curl = sources_module.CurlSource.from_args(["--service-fd", str(sock.fileno())])
    curl.cache = tmp_path / "curl-cache"
    curl.cache.mkdir(parents=True, exist_ok=True)

    curl.fetch_many(TEST_SOURCE_PAIRS)
    for chksum, desc in TEST_SOURCE_PAIRS:
        assert (curl.cache / chksum).exists()
        assert verify_file(curl.cache / chksum, chksum)
