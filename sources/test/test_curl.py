#!/usr/bin/python3

import pathlib
import socket
import subprocess
from unittest.mock import patch

SOURCES_NAME = "org.osbuild.curl"

hashes = {
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855": b"",
    "5feceb66ffc86f38d952786c6d696c79c2dbc239dd4e91b46729d73a27fb57e9": b"0",
    "6b86b273ff34fce19d6b804eff5a3f5747ada4eaa22f1d49c01e52ddb7875b4b": b"1",
    "d4735e3a265e16eee03f59718b9b5d03019c07d8b6c51f90da3a666eec13ab35": b"2",
    "4e07408562bedb8b60ce05c1decfe3ad16b72230967de01f640b7e4729b49fce": b"3",
    "4b227777d4dd1fc61c6f884f48641d02b4d121d3fd328cb08b5531fcacdabf8a": b"4",
    "ef2d127de37b942baad06145e54b0c619a1f22327b2ebbcfbec78f5564afe39d": b"5",
    "e7f6c011776e8db7cd330b54174fd76f7d0216b612387a5ffcfb81e6f0919683": b"6",
    "7902699be42c8a8e46fbbb4501726517e86b22c56a189f7625a6da49081b2451": b"7",
    "2c624232cdd221771294dfbb310aca000a0df6ac8b66b696d90ef06fdefb64a3": b"8",
    "19581e27de7ced00ff1ce50b2047e7a567c76b1cbaebabe5ef03f7c3017bb5b7": b"9",
}


def fake_download(*args, **kwargs):
    curl_argv = args[0]
    output = curl_argv[curl_argv.index("--output") + 1]
    content = hashes[output.split(":")[1]]
    target_filename = pathlib.Path(kwargs["cwd"], output)
    target_filename.write_bytes(content)
    return subprocess.CompletedProcess(args, 0)


@patch("subprocess.run")
def test_curl_fetch_one(mocked_run, tmp_path, sources_module):
    mocked_run.side_effect = fake_download
    
    # source will automatically close the socket on __del__()
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    curl = sources_module.CurlSource.from_args(["--service-fd", str(sock.fileno())])
    curl.cache = tmp_path / "curl-cache"
    curl.cache.mkdir(parents=True, exist_ok=True)
    assert curl is not None
    desc = {
        "url": "http://example.com/file1",
    }
    requested_file = "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    curl.fetch_all({requested_file: desc})
    assert (curl.cache / requested_file).exists()
