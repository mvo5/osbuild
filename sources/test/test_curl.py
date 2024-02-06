#!/usr/bin/python3

import textwrap

SOURCES_NAME = "org.osbuild.curl"


TEST_SOURCE_PAIRS = [
    (
        "sha256:5feceb66ffc86f38d952786c6d696c79c2dbc239dd4e91b46729d73a27fb57e9",
        {
            "url": "http://example.com/file0",
        },
    ), (
        "sha256:6b86b273ff34fce19d6b804eff5a3f5747ada4eaa22f1d49c01e52ddb7875b4b",
        {
            "url": "http://example.com/file1",
            "insecure": True,
        },
    ), (
        "sha256:d4735e3a265e16eee03f59718b9b5d03019c07d8b6c51f90da3a666eec13ab35",
        {
            "url": "http://example.com/file2",
            "secrets": {
                "ssl_ca_cert": "some-ssl_ca_cert",
            },
        },
    ), (
        "sha256:4e07408562bedb8b60ce05c1decfe3ad16b72230967de01f640b7e4729b49fce",
        {
            "url": "http://example.com/file3",
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
