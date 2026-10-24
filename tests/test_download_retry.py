import hashlib
import time
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Callable, Iterator
from unittest.mock import patch

import pytest
import requests

from bebraland_frontend import runtime
from bebraland_frontend.runtime import download_file, set_instances_root, sync_manifest

PAYLOAD = b"mod-bytes"
PAYLOAD_SHA256 = hashlib.sha256(PAYLOAD).hexdigest()


class FakeResponse:
    def __init__(self, chunks: Callable[[], Iterator[bytes]], status_code: int = 200) -> None:
        self.chunks = chunks
        self.status_code = status_code
        self.headers: dict[str, str] = {}

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *args: Any) -> None:
        return None

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code} error", response=self)

    def iter_content(self, chunk_size: int) -> Iterator[bytes]:
        return self.chunks()


def ok_response() -> FakeResponse:
    return FakeResponse(lambda: iter([PAYLOAD]))


def test_download_retries_after_network_error() -> None:
    with TemporaryDirectory() as tmp, patch.object(runtime, "DOWNLOAD_RETRY_DELAY_SECONDS", 0):
        dest = Path(tmp) / "mods" / "a.jar"
        responses = [requests.ConnectionError("connection reset"), ok_response()]

        def fake_get(*args: Any, **kwargs: Any) -> FakeResponse:
            result = responses.pop(0)
            if isinstance(result, Exception):
                raise result
            return result

        with patch.object(runtime.requests, "get", side_effect=fake_get) as get:
            download_file("https://example/a.jar", dest, PAYLOAD_SHA256, lambda _: None)

        assert get.call_count == 2
        assert dest.read_bytes() == PAYLOAD


def test_download_does_not_retry_client_errors() -> None:
    with TemporaryDirectory() as tmp, patch.object(runtime, "DOWNLOAD_RETRY_DELAY_SECONDS", 0):
        dest = Path(tmp) / "mods" / "a.jar"
        missing = FakeResponse(lambda: iter([]), status_code=404)

        with patch.object(runtime.requests, "get", return_value=missing) as get:
            with pytest.raises(requests.HTTPError):
                download_file("https://example/a.jar", dest, PAYLOAD_SHA256, lambda _: None)

        assert get.call_count == 1
        assert not dest.with_suffix(".jar.part").exists()


def test_sync_stops_other_downloads_after_failure() -> None:
    def slow_chunks() -> Iterator[bytes]:
        for _ in range(200):
            time.sleep(0.05)
            yield b"x"

    def fake_get(url: str, *args: Any, **kwargs: Any) -> FakeResponse:
        if url.endswith("bad.jar"):
            time.sleep(0.2)
            return FakeResponse(lambda: iter([]), status_code=404)
        return FakeResponse(slow_chunks)

    manifest = {
        "profile": {"slug": "pack"},
        "files": [
            {"path": "mods/slow.jar", "sha256": PAYLOAD_SHA256, "url": "https://example/slow.jar", "size": 200},
            {"path": "mods/bad.jar", "sha256": PAYLOAD_SHA256, "url": "https://example/bad.jar", "size": 1},
        ],
    }
    with TemporaryDirectory() as tmp:
        set_instances_root(tmp)
        try:
            started = time.monotonic()
            with patch.object(runtime.requests, "get", side_effect=fake_get):
                with pytest.raises(requests.HTTPError):
                    sync_manifest(manifest, "https://example", lambda _: None)
            elapsed = time.monotonic() - started
        finally:
            set_instances_root(None)

        assert elapsed < 3
        assert not (Path(tmp) / "pack" / "mods" / "slow.jar.part").exists()
