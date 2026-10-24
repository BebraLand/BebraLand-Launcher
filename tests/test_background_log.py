import threading
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from bebraland_frontend import app
from bebraland_frontend.app import BackgroundLog


def test_writes_lines_in_order_and_flushes_on_close() -> None:
    with TemporaryDirectory() as tmp:
        path = Path(tmp) / "logs" / "launcher.log"
        log = BackgroundLog(path)
        for index in range(200):
            log.write(f"line {index}")
        log.close()

        lines = path.read_text(encoding="utf-8").splitlines()
        assert [line.split("] ", 1)[1] for line in lines] == [f"line {index}" for index in range(200)]


def test_write_does_not_wait_for_a_blocked_output() -> None:
    release = threading.Event()

    def blocked_print(*args: object, **kwargs: object) -> None:
        release.wait(5)

    with TemporaryDirectory() as tmp, patch.object(app, "print", blocked_print, create=True):
        log = BackgroundLog(Path(tmp) / "launcher.log")
        finished = threading.Event()

        def writer() -> None:
            for index in range(50):
                log.write(f"line {index}")
            finished.set()

        threading.Thread(target=writer).start()
        assert finished.wait(1)
        release.set()
        log.close()
