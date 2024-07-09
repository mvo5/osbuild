#!/usr/bin/python3
"""
network related utilities
"""
import contextlib
import http.server
import ssl
import socket
import threading

try:
    from http.server import ThreadingHTTPServer
except ImportError:
    # This fallback is only needed on py3.6. Py3.7+ has ThreadingHTTPServer.
    # We just import ThreadingHTTPServer here so that the import of "net.py"
    # on py36 works, the helpers are not usable because the "directory" arg
    # for SimpleHTTPRequestHandler is also not supported.
    class ThreadingHTTPServer:  # type: ignore
        def __init__(self, *args, **kwargs):  # pylint: disable=unused-argument
            # pylint: disable=import-outside-toplevel
            import pytest  # type: ignore
            pytest.skip("python too old to suport ThreadingHTTPServer")


from .atomic import AtomicCounter


def _get_free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("localhost", 0))
    return s.getsockname()[1]


class SilentHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args, **kwargs):
        pass

    def do_GET(self):
        # silence errors when the other side "hangs up" unexpectedly
        # (our tests will do that when downloading in parallel)
        try:
            super().do_GET()
        except (ConnectionResetError, BrokenPipeError):
            pass


class DirHTTPServer(ThreadingHTTPServer):
    def __init__(self, *args, directory=None, simulate_failures=0, **kwargs):
        super().__init__(*args, **kwargs)
        self.directory = directory
        self.simulate_failures = AtomicCounter(simulate_failures)
        self.reqs = AtomicCounter()

    def finish_request(self, request, client_address):
        self.reqs.inc()
        if self.simulate_failures.count > 0:
            self.simulate_failures.dec()
            SilentHTTPRequestHandler(
                request, client_address, self, directory="does-not-exists")
            return
        SilentHTTPRequestHandler(
            request, client_address, self, directory=self.directory)


def _httpd(rootdir, port, simulate_failures):
    return DirHTTPServer(
        ("localhost", port),
        http.server.SimpleHTTPRequestHandler,
        directory=rootdir,
        simulate_failures=simulate_failures,
    )


@contextlib.contextmanager
def http_serve_directory(rootdir, simulate_failures=0):
    port = _get_free_port()
    httpd = _httpd(rootdir, port, simulate_failures)
    threading.Thread(target=httpd.serve_forever).start()
    try:
        yield httpd
    finally:
        httpd.shutdown()


@contextlib.contextmanager
def https_serve_directory(rootdir, certfile, keyfile, simulate_failures=0):
    port = _get_free_port()
    httpd = _httpd(rootdir, port, simulate_failures)

    ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ctx.load_cert_chain(certfile=certfile, keyfile=keyfile)
    httpd.socket = ctx.wrap_socket(httpd.socket, server_side=True)

    t = threading.Thread(target=httpd.serve_forever)
    t.start()
    try:
        yield httpd
    finally:
        httpd.shutdown()
        t.join()
