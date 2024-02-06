#!/usr/bin/python3

import pathlib
import socket
import subprocess
import textwrap
from unittest.mock import patch

import pytest

SOURCES_NAME = "org.osbuild.curl"

# hashes = {
#     "5feceb66ffc86f38d952786c6d696c79c2dbc239dd4e91b46729d73a27fb57e9": b"0",
#     "6b86b273ff34fce19d6b804eff5a3f5747ada4eaa22f1d49c01e52ddb7875b4b": b"1",
#     "d4735e3a265e16eee03f59718b9b5d03019c07d8b6c51f90da3a666eec13ab35": b"2",
#     "4e07408562bedb8b60ce05c1decfe3ad16b72230967de01f640b7e4729b49fce": b"3",
#     "4b227777d4dd1fc61c6f884f48641d02b4d121d3fd328cb08b5531fcacdabf8a": b"4",
#     "ef2d127de37b942baad06145e54b0c619a1f22327b2ebbcfbec78f5564afe39d": b"5",
#     "e7f6c011776e8db7cd330b54174fd76f7d0216b612387a5ffcfb81e6f0919683": b"6",
#     "7902699be42c8a8e46fbbb4501726517e86b22c56a189f7625a6da49081b2451": b"7",
#     "2c624232cdd221771294dfbb310aca000a0df6ac8b66b696d90ef06fdefb64a3": b"8",
#     "19581e27de7ced00ff1ce50b2047e7a567c76b1cbaebabe5ef03f7c3017bb5b7": b"9",
# }


# def fake_download(*args, **kwargs):
#     curl_argv = args[0]
#     output = curl_argv[curl_argv.index("--output") + 1]
#     content = hashes[output.split(":")[1]]
#     target_filename = pathlib.Path(kwargs["cwd"], output)
#     target_filename.write_bytes(content)
#     return subprocess.CompletedProcess(args, 0)


# @patch("subprocess.run")
# def test_curl_fetch_all_integration(mocked_run, tmp_path, sources_module):
#     mocked_run.side_effect = fake_download
    
#     # source will automatically close the socket on __del__()
#     sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
#     curl = sources_module.CurlSource.from_args(["--service-fd", str(sock.fileno())])
#     curl.cache = tmp_path / "curl-cache"
#     curl.cache.mkdir(parents=True, exist_ok=True)
#     assert curl is not None
#     desc = {
#         "url": "http://example.com/file1",
#     }
#     requested_file = "sha256:6b86b273ff34fce19d6b804eff5a3f5747ada4eaa22f1d49c01e52ddb7875b4b"
#     curl.fetch_all({requested_file: desc})
#     assert (curl.cache / requested_file).exists()


TEST_SOURCE_ITEMS = {
    "sha256:5feceb66ffc86f38d952786c6d696c79c2dbc239dd4e91b46729d73a27fb57e9": {
        "url": "http://example.com/file0",
    },
    "sha256:6b86b273ff34fce19d6b804eff5a3f5747ada4eaa22f1d49c01e52ddb7875b4b": {
        "url": "http://example.com/file1",
        "insecure": True,
    },
    "sha256:d4735e3a265e16eee03f59718b9b5d03019c07d8b6c51f90da3a666eec13ab35": {
        "url": "http://example.com/file2",
        "secrets": {
            "ssl_ca_cert": "some-ssl_ca_cert",
        },
    },
    "sha256:4e07408562bedb8b60ce05c1decfe3ad16b72230967de01f640b7e4729b49fce": {
        "url": "http://example.com/file3",
        "secrets": {
            "ssl_client_cert": "some-ssl_client_cert",
            "ssl_client_key": "some-ssl_client_key",
        },
    },
}


def test_curl_gen_download_config(tmp_path, sources_module):
    dst_path = tmp_path / "curl-config.txt"
    sources_module._gen_curl_download_config(TEST_SOURCE_ITEMS, dst_path)
    assert dst_path.exists()
    assert dst_path.read_text(encoding="utf8") == textwrap.dedent(f"""\
    url = "http://example.com/file0"
    output = "sha256:5feceb66ffc86f38d952786c6d696c79c2dbc239dd4e91b46729d73a27fb57e9"
    no-insecure

    url = "http://example.com/file1"
    output = "sha256:6b86b273ff34fce19d6b804eff5a3f5747ada4eaa22f1d49c01e52ddb7875b4b"
    insecure

    url = "http://example.com/file2"
    output = "sha256:d4735e3a265e16eee03f59718b9b5d03019c07d8b6c51f90da3a666eec13ab35"
    cacert = "some-ssl_ca_cert"
    no-insecure

    url = "http://example.com/file3"
    output = "sha256:4e07408562bedb8b60ce05c1decfe3ad16b72230967de01f640b7e4729b49fce"
    cert = "some-ssl_client_cert"
    key = "some-ssl_client_key"
    no-insecure

    """)


@pytest.mark.parametrize("curl_ver,expected", [
    ("curl 1.0.1 fbar", False),
    ("curl 8.0.2 random other", True),
    ("curl 7.65.1 random stuff", False),
    ("curl 7.68.0 random stuff", True),
])
@patch("subprocess.check_output")
def test_curl_has_parallel_downloads(mocked_run, sources_module, curl_ver, expected):
    mocked_run.return_value = curl_ver
    assert sources_module._curl_has_parallel_downloads() == expected
