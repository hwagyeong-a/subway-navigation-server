"""E2E test infrastructure.

`live_server` 픽스처가 실제 Flask 개발 서버를 subprocess 로 띄우고
모든 E2E 테스트가 해당 base_url 을 공유한다.
"""
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest
import requests


REPO_ROOT = Path(__file__).resolve().parents[2]


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="session")
def live_server():
    """실 Flask 서버를 subprocess 로 띄우고 base_url 반환."""
    port = _free_port()
    env = {
        **os.environ,
        "FLASK_HOST": "127.0.0.1",
        "FLASK_PORT": str(port),
        "FLASK_DEBUG": "0",
    }
    proc = subprocess.Popen(
        [sys.executable, "app.py"],
        cwd=REPO_ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    base_url = f"http://127.0.0.1:{port}"
    deadline = time.time() + 15
    while time.time() < deadline:
        try:
            r = requests.get(f"{base_url}/health", timeout=1)
            if r.status_code == 200:
                break
        except requests.exceptions.RequestException:
            time.sleep(0.3)
    else:
        proc.terminate()
        out, err = proc.communicate(timeout=2)
        raise RuntimeError(
            "Live server did not become healthy.\n"
            f"stdout: {out.decode(errors='replace')}\n"
            f"stderr: {err.decode(errors='replace')}"
        )

    yield base_url

    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """Playwright: 한국어 환경 + 일관된 viewport."""
    return {
        **browser_context_args,
        "locale": "ko-KR",
        "viewport": {"width": 1280, "height": 800},
    }
