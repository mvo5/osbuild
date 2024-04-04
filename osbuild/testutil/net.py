#!/usr/bin/python3
"""
network related utilities
"""
import contextlib
import http.server
import socket
import time
import threading

def wait_port_ready(address, port, sleep=1, max_wait_sec=30):
    for i in range(int(max_wait_sec / sleep)):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(sleep)
            try:
                s.connect((address, port))
                return
            except (ConnectionRefusedError, ConnectionResetError, TimeoutError) as e:
                pass
            time.sleep(sleep)
    raise ConnectionRefusedError(f"cannot connect to port {port} after {max_wait_sec}s")


def _get_free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("localhost", 0))
    return s.getsockname()[1]


class SilentHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args, **kwargs):
        pass


class DirHTTPServer(http.server.ThreadingHTTPServer):
    def __init__(self, *args, directory=None, simulate_failures=0, **kwargs):
        super().__init__(*args, **kwargs)
        self.directory = directory
        self.simulate_failures = simulate_failures
        self.reqs = 0

    def finish_request(self, request, client_address):
        self.reqs += 1  # racy on non GIL systems
        if self.simulate_failures > 0:
            self.simulate_failures -= 1  # racy on non GIL systems
            SilentHTTPRequestHandler(
                request, client_address, self, directory="does-not-exists")
            return
        SilentHTTPRequestHandler(
            request, client_address, self, directory=self.directory)


@contextlib.contextmanager
def http_serve_directory(rootdir, simulate_failures=0):
    port = _get_free_port()
    httpd = DirHTTPServer(
        ("localhost", port),
        http.server.SimpleHTTPRequestHandler,
        directory=rootdir,
        simulate_failures=simulate_failures,
    )
    threading.Thread(target=httpd.serve_forever).start()
    wait_port_ready("localhost", port)
    try:
        yield httpd
    finally:
        httpd.shutdown()
