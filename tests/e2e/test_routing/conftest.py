import time
from pathlib import Path
from typing import Callable

import httpx
import psutil
import pytest
from _pytest.fixtures import FixtureRequest
from _pytest.monkeypatch import MonkeyPatch


@pytest.fixture()
def run_server(tmp_path: Path, request: FixtureRequest, monkeypatch: MonkeyPatch) -> Callable[[str, list[str]], None]:
    def runner(app: str, server_command: list[str]) -> None:
        tmp_path.joinpath("app.py").write_text(app)
        monkeypatch.chdir(tmp_path)

        proc = psutil.Popen(server_command)

        def kill() -> None:
            for child in proc.children(recursive=True):
                child.kill()
            proc.kill()
            proc.wait()

        request.addfinalizer(kill)

        for _ in range(50):
            try:
                httpx.get("http://127.0.0.1:9999/", timeout=0.1)
                break
            except httpx.TransportError:
                time.sleep(0.1)
        else:
            raise RuntimeError("App failed to come online")

    return runner
