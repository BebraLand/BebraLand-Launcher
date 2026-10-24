import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Iterator
from unittest.mock import patch

from bebraland_frontend import runtime
from bebraland_frontend.runtime import set_instances_root, sync_manifest

PAYLOAD = b"mod-bytes"
PAYLOAD_SHA256 = hashlib.sha256(PAYLOAD).hexdigest()
MANIFEST = {
    "profile": {"slug": "pack"},
    "files": [{"path": "mods/a.jar", "sha256": PAYLOAD_SHA256, "url": "https://example/a.jar", "size": len(PAYLOAD)}],
}


class FakeResponse:
    headers: dict[str, str] = {}

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *args: Any) -> None:
        return None

    def raise_for_status(self) -> None:
        return None

    def iter_content(self, chunk_size: int) -> Iterator[bytes]:
        return iter([PAYLOAD])


def sync(fake_get: Any) -> None:
    with patch.object(runtime.requests, "get", side_effect=fake_get):
        sync_manifest(MANIFEST, "https://example", lambda _: None)


def test_unchanged_files_are_not_rehashed() -> None:
    with TemporaryDirectory() as tmp:
        set_instances_root(tmp)
        try:
            sync(lambda *args, **kwargs: FakeResponse())
            with patch.object(runtime, "sha256_file", wraps=runtime.sha256_file) as sha256_file:
                sync(lambda *args, **kwargs: FakeResponse())
        finally:
            set_instances_root(None)

        assert sha256_file.call_count == 0


def test_changed_file_is_rehashed_and_downloaded_again() -> None:
    with TemporaryDirectory() as tmp:
        set_instances_root(tmp)
        try:
            sync(lambda *args, **kwargs: FakeResponse())
            target = Path(tmp) / "pack" / "mods" / "a.jar"
            target.write_bytes(b"broken")

            downloads: list[str] = []

            def fake_get(url: str, *args: Any, **kwargs: Any) -> FakeResponse:
                downloads.append(url)
                return FakeResponse()

            sync(fake_get)
        finally:
            set_instances_root(None)

        assert downloads == ["https://example/a.jar"]
        assert target.read_bytes() == PAYLOAD
