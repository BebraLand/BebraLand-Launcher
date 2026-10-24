import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Callable, Iterator
from contextlib import contextmanager

import requests

from bebraland_frontend.runtime import track_streamed_request_bytes

PAYLOAD = b"x" * 1000


@contextmanager
def payload_server() -> Iterator[str]:
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def do_GET(self) -> None:
            self.send_response(200)
            self.send_header("Content-Length", str(len(PAYLOAD)))
            self.end_headers()
            self.wfile.write(PAYLOAD)

        def log_message(self, *args: Any) -> None:
            return None

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/file"
    finally:
        server.shutdown()
        server.server_close()


def on_other_thread(fn: Callable[[], Any]) -> None:
    thread = threading.Thread(target=fn)
    thread.start()
    thread.join()


def test_counts_only_install_traffic() -> None:
    counted: list[int] = []
    with payload_server() as url, track_streamed_request_bytes(counted.append):
        assert requests.get(url, stream=True).content == PAYLOAD
        install_total = sum(counted)

        library_session = requests.session()
        on_other_thread(lambda: library_session.get(url, stream=True).content)
        library_total = sum(counted) - install_total

        before_foreign = sum(counted)
        on_other_thread(lambda: requests.get(url, stream=True).content)
        on_other_thread(lambda: requests.Session().get(url, stream=True).content)
        foreign_total = sum(counted) - before_foreign

    assert install_total == len(PAYLOAD)
    assert library_total == len(PAYLOAD)
    assert foreign_total == 0


def test_restores_requests_after_install() -> None:
    original_get, original_session = requests.get, requests.session
    with track_streamed_request_bytes(lambda _: None):
        assert requests.get is not original_get
    assert requests.get is original_get
    assert requests.session is original_session
