import configparser
import importlib
import json
import os
import socket
import subprocess as sp
import sys
from tempfile import TemporaryDirectory

import pytest

REPO_PATHS = [
    "./test/data/testrepos/baseos/",
    "./test/data/testrepos/custom/",
]

# osbuild-depsolve-dnf uses the GPG header to detect if keys are defined in-line or as file paths/URLs
TEST_KEY = "-----BEGIN PGP PUBLIC KEY BLOCK-----\nTEST KEY\n"


def has_dnf5():
    return bool(importlib.util.find_spec("libdnf5"))


# XXX: super nitpick^:googol:) sorry, I'm sure I'm annoying at this
# point :( I wonder if tweaking the order of the arguments might make
# sense? There is no real standard here and it's super subjective so
# feel free to stop reading here :)
#
#My thinking is mostly that typically "more static" things come first,
#then the more changing things. e.g. in golang typically each thing
#that takes a context takes it first. Here that might be:
#
#    def depsolve(root_dir, cache_dir, command, repos, pkgs):
#
#but I'm probably totally overthing it, probably best to ignore me here
def depsolve(pkgs, repos, root_dir, cache_dir, command):
    req = {
        "command": "depsolve",
        "arch": "x86_64",
        "module_platform_id": "platform:el9",
        "releasever": "9",
        "cachedir": cache_dir,
        "arguments": {
            "root_dir": root_dir,
            "repos": repos,
            "transactions": [
                {"package-specs": pkgs},
            ]
        }
    }
    p = sp.run([command], input=json.dumps(req).encode(), check=True, stdout=sp.PIPE, stderr=sys.stderr)

    return json.loads(p.stdout.decode())


def get_rand_port():
    s = socket.socket()
    s.bind(("", 0))
    return s.getsockname()[1]


@pytest.fixture(name="repo_servers", scope="module")
def repo_servers_fixture():
    procs = []
    addresses = []
    for path in REPO_PATHS:
        port = get_rand_port()  # this is racy, but should be okay
        p = sp.Popen(["python3", "-m", "http.server", str(port)], cwd=path, stdout=sp.PIPE, stderr=sp.DEVNULL)
        procs.append(p)
        # use last path component as name
        name = os.path.basename(path.rstrip("/"))
        addresses.append({"name": name, "address": f"http://localhost:{port}"})
    yield addresses
    for p in procs:
        p.kill()


# XXX: try a more pytest-ish pattern: (idle rambling) pytest seems to
# encourage a pattern like input, expected for the paramterization,
# but of course the test cases would have to change to become
# pairs. Then the test cases are harder to read so it's a bit of a
# wash but I wanted to mention it as I was thinking about it :)
test_cases = [
    {
        "packages": ["filesystem"],
        "results": {
            "basesystem",
            "bash",
            "centos-gpg-keys",
            "centos-stream-release",
            "centos-stream-repos",
            "filesystem",
            "glibc",
            "glibc-common",
            "glibc-minimal-langpack",
            "libgcc",
            "ncurses-base",
            "ncurses-libs",
            "setup",
            "tzdata",
        }
    },
    {
        # "pkg-with-no-deps" is the only package in the custom repo and has no dependencies
        "packages": ["pkg-with-no-deps"],
        "results": {
            "pkg-with-no-deps",
        }
    },
    {
        "packages": ["filesystem", "pkg-with-no-deps"],
        "results": {
            "basesystem",
            "bash",
            "centos-gpg-keys",
            "centos-stream-release",
            "centos-stream-repos",
            "filesystem",
            "glibc",
            "glibc-common",
            "glibc-minimal-langpack",
            "libgcc",
            "ncurses-base",
            "ncurses-libs",
            "setup",
            "tzdata",
            "pkg-with-no-deps"
        }
    },
    {
        "packages": ["tmux", "pkg-with-no-deps"],
        "results": {
            "alternatives",
            "basesystem",
            "bash",
            "ca-certificates",
            "centos-gpg-keys",
            "centos-stream-release",
            "centos-stream-repos",
            "coreutils",
            "coreutils-common",
            "crypto-policies",
            "filesystem",
            "glibc",
            "glibc-common",
            "glibc-minimal-langpack",
            "gmp",
            "grep",
            "libacl",
            "libattr",
            "libcap",
            "libevent",
            "libffi",
            "libgcc",
            "libselinux",
            "libsepol",
            "libsigsegv",
            "libtasn1",
            "ncurses-base",
            "ncurses-libs",
            "openssl-libs",
            "p11-kit",
            "p11-kit-trust",
            "pcre",
            "pcre2",
            "pcre2-syntax",
            "sed",
            "setup",
            "tmux",
            "tzdata",
            "zlib",
            "pkg-with-no-deps",
        }
    },
]


def enum_repo_configs(servers):
    """
    Return all configurations for the provided repositories, either as config files in a directory or as repository
    configs in the depsolve request, or a combination of both.
    """
    # we only have two servers, so let's just enumerate all the combinations
    combo_idxs = [
        ((0, 1), ()),  # all in req
        ((0,), (1,)),    # one in req and one in dir
        ((1,), (0,)),    # same but flipped
        ((), (0, 1)),  # all in dir
    ]
    for combo in combo_idxs:
        repo_configs = []
        for idx in combo[0]:  # servers to be configured through request
            server = servers[idx]
            repo_configs.append({
                "id": server["name"],
                "name": server["name"],
                "baseurl": server["address"],
                "check_gpg": False,
                "ignoressl": True,
                "rhsm": False,
                "gpgkeys": [TEST_KEY],
            })
        with TemporaryDirectory() as root_dir:
            repos_dir = os.path.join(root_dir, "etc/yum.repos.d")
            os.makedirs(repos_dir)
            keys_dir = os.path.join(root_dir, "etc/pki/rpm-gpg")
            os.makedirs(keys_dir)
            vars_dir = os.path.join(root_dir, "etc/dnf/vars")
            os.makedirs(vars_dir)

            # Use the gpgkey to test both the key reading and the variable substitution.
            # For this test, it doesn't need to be a real key.
            key_url = "file:///etc/pki/rpm-gpg/RPM-GPG-KEY-$releasever-$basearch-$customvar"

            customvar = "test-customvar"
            key_path = os.path.join(keys_dir, f"RPM-GPG-KEY-9-x86_64-{customvar}")
            with open(key_path, "w", encoding="utf-8") as key_file:
                key_file.write(TEST_KEY)

            vars_path = os.path.join(vars_dir, "customvar")
            with open(vars_path, "w", encoding="utf-8") as vars_file:
                vars_file.write(customvar)

            for idx in combo[1]:  # servers to be configured through root_dir
                server = servers[idx]
                parser = configparser.ConfigParser()
                name = server["name"]
                parser.add_section(name)
                # Set some options in a specific order in which they tend to be
                # written in repo files.
                parser.set(name, "name", name)
                parser.set(name, "baseurl", server["address"])
                parser.set(name, "enabled", "1")
                parser.set(name, "gpgcheck", "1")
                parser.set(name, "sslverify", "0")
                parser.set(name, "gpgkey", key_url)

                with open(f"{repos_dir}/{name}.repo", "w", encoding="utf-8") as repo_file:
                    parser.write(repo_file, space_around_delimiters=False)

            yield repo_configs, root_dir


@pytest.fixture(name="cache_dir", scope="session")
def cache_dir_fixture(tmpdir_factory):
    return str(tmpdir_factory.mktemp("cache"))


def _test_depsolve_both_dnf_dnf5(command, repo_servers, test_case, cache_dir):
    pks = test_case["packages"]

    for repo_configs, root_dir in enum_repo_configs(repo_servers):
        res = depsolve(pks, repo_configs, root_dir, cache_dir, command)
        assert {pkg["name"] for pkg in res["packages"]} == test_case["results"]
        for repo in res["repos"].values():
            assert repo["gpgkeys"] == [TEST_KEY]


@pytest.mark.parametrize("test_case", test_cases)
def test_depsolve(repo_servers, test_case, cache_dir):
    command = "./tools/osbuild-depsolve-dnf"
    _test_depsolve_both_dnf_dnf5(command, repo_servers, test_case, cache_dir)


@pytest.mark.skipif(not has_dnf5(), reason="libdnf5 not available")
@pytest.mark.parametrize("test_case", test_cases)
def test_depsolve_dnf5(repo_servers, test_case, cache_dir):
    command = "./tools/osbuild-depsolve-dnf5"
    _test_depsolve_both_dnf_dnf5(command, repo_servers, test_case, cache_dir)
