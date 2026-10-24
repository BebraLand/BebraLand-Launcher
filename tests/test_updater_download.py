import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Iterator
from unittest.mock import patch

import pytest
import requests

from bebraland_frontend import updater
from bebraland_frontend.updater import download_release

PAYLOAD = b"launcher-binary"
RELEASE = {
    "version": "1.2.3",
    "url": "https://example/BebraLandLauncher.exe",
    "sha256": hashlib.sha256(PAYLOAD).hexdigest(),
}


class FakeResponse:
    def __init__(self, status_code: int = 200) -> None:
        self.status_code = status_code
        self.headers = {"content-length": str(len(PAYLOAD))}

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *args: Any) -> None:
        return None

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code} error", response=self)

    def iter_content(self, chunk_size: int) -> Iterator[bytes]:
        return iter([PAYLOAD])


def test_release_download_retries_and_reports_progress() -> None:
    responses: list[Any] = [requests.ConnectionError("connection reset"), FakeResponse()]

    def fake_get(*args: Any, **kwargs: Any) -> FakeResponse:
        result = responses.pop(0)
        if isinstance(result, Exception):
            raise result
        return result

    progress: list[tuple[int, int, str]] = []
    with TemporaryDirectory() as tmp, patch.object(updater, "launcher_data_dir", return_value=Path(tmp)), \
            patch.object(updater, "UPDATE_RETRY_DELAY_SECONDS", 0), \
            patch.object(updater.requests, "get", side_effect=fake_get) as get:
        downloaded = download_release(RELEASE, lambda _: None, lambda *args: progress.append(args))
        assert downloaded.read_bytes() == PAYLOAD

    assert get.call_count == 2
    assert progress[-1][:2] == (len(PAYLOAD), len(PAYLOAD))
    assert progress[-1][2].startswith("Download launcher 1.2.3 - ")


def test_release_download_does_not_retry_missing_file() -> None:
    with TemporaryDirectory() as tmp, patch.object(updater, "launcher_data_dir", return_value=Path(tmp)), \
            patch.object(updater, "UPDATE_RETRY_DELAY_SECONDS", 0), \
            patch.object(updater.requests, "get", return_value=FakeResponse(404)) as get:
        with pytest.raises(requests.HTTPError):
            download_release(RELEASE, lambda _: None)

    assert get.call_count == 1
