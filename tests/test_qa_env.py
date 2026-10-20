# -*- coding: utf-8 -*-
"""
qa.py 가 검사를 실행하지 못할 때의 계약 — exit 2 와 다음 명령 한 줄.

Chromium 이 없을 때 Playwright 의 설치 안내 상자가 그대로 출력되고 traceback 이 따라붙었다.
exit 1 이라 「문서가 검사에 실패하였다」와 구분되지 않았고, 사용자는 무엇을 실행해야 하는지
알 수 없었다. 환경 문제는 문서를 고쳐도 해결되지 않으므로 종료 코드부터 달라야 한다.
"""
import importlib.util
import os
import subprocess
import sys

import pytest
from conftest import ASSETS, ROOT

qa = pytest.importorskip("qa")

ENTRY_POINTS = [ASSETS / "qa.py", ROOT / "scripts" / "qa.py"]

# Playwright 1.60 이 Chromium 실행 파일이 없을 때 던지는 메시지 그대로다.
MISSING_BROWSER = (
    "BrowserType.launch: Executable doesn't exist at /x/chromium_headless_shell-1223/"
    "chrome-headless-shell-mac-arm64/chrome-headless-shell\n"
    "╔════════════════════════════════════════════════════════════╗\n"
    "║ Looks like Playwright was just installed or updated.       ║\n"
    "║ Please run the following command to download new browsers: ║\n"
    "║                                                            ║\n"
    "║     playwright install                                     ║\n"
    "║                                                            ║\n"
    "║ <3 Playwright Team                                         ║\n"
    "╚════════════════════════════════════════════════════════════╝"
)


class _FakePlaywright:
    """sync_playwright() 자리에 놓는다. chromium.launch() 가 주어진 예외를 던진다."""

    def __init__(self, exc):
        self.exc = exc
        self.chromium = self

    def __call__(self):
        return self

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def launch(self, **_):
        raise self.exc


def _playwright_error(message):
    from playwright.sync_api import Error

    return Error(message)


@pytest.fixture
def target(tmp_path):
    p = tmp_path / "doc.html"
    p.write_text('<html data-mode="paper"><body></body></html>', encoding="utf-8")
    return p


def test_exit_codes_are_distinct():
    assert (qa.EXIT_OK, qa.EXIT_FAILED, qa.EXIT_NOT_READY) == (0, 1, 2)


def test_missing_chromium_exits_2_with_one_line_hint(target, monkeypatch, capsys):
    monkeypatch.setattr(qa, "sync_playwright", _FakePlaywright(_playwright_error(MISSING_BROWSER)))
    monkeypatch.setattr(sys, "argv", ["qa.py", str(target)])
    assert qa.main() == qa.EXIT_NOT_READY
    out = capsys.readouterr()
    lines = out.err.strip().splitlines()
    assert len(lines) == 1, f"안내가 한 줄이 아니다: {lines}"
    assert "-m playwright install chromium" in lines[0]
    assert "Chromium" in lines[0]
    assert "╔" not in out.err + out.out, "Playwright 의 설치 안내 상자가 그대로 출력되었다"


def test_other_launch_errors_are_not_reported_as_missing_chromium(target, monkeypatch):
    """감지가 넓으면 다른 실패를 「Chromium 설치」로 잘못 안내한다. 그대로 던져야 한다."""
    err = _playwright_error("BrowserType.launch: Target page, context or browser has been closed")
    monkeypatch.setattr(qa, "sync_playwright", _FakePlaywright(err))
    with pytest.raises(type(err)):
        qa.run(target, None, None)


def test_missing_system_dependencies_are_not_reported_as_missing_chromium():
    """`install-deps` 는 시스템 라이브러리 문제다. `install chromium` 으로는 해결되지 않는다."""
    msg = "Host system is missing dependencies to run browsers.\n║ sudo playwright install-deps ║"
    assert not qa.browser_missing(Exception(msg))
    assert qa.browser_missing(Exception(MISSING_BROWSER))


def test_missing_playwright_package_exits_2(target, monkeypatch, capsys):
    monkeypatch.setattr(qa, "sync_playwright", None)
    monkeypatch.setattr(sys, "argv", ["qa.py", str(target)])
    assert qa.main() == qa.EXIT_NOT_READY
    err = capsys.readouterr().err.strip().splitlines()
    assert len(err) == 1 and "-m pip install playwright" in err[0], err


def test_wrapper_shares_the_contract(target, monkeypatch, capsys):
    """`scripts/qa.py` 는 구현을 따로 불러온다. 같은 main 이 같은 코드를 돌려주는지 본다."""
    spec = importlib.util.spec_from_file_location("_scripts_qa", ROOT / "scripts" / "qa.py")
    wrapper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(wrapper)
    impl = wrapper._MODULE
    monkeypatch.setattr(impl, "sync_playwright", _FakePlaywright(_playwright_error(MISSING_BROWSER)))
    monkeypatch.setattr(sys, "argv", ["qa.py", str(target)])
    assert wrapper.main() == 2
    assert "-m playwright install chromium" in capsys.readouterr().err


@pytest.mark.parametrize("entry", ENTRY_POINTS, ids=lambda p: str(p.relative_to(ROOT)))
def test_missing_target_exits_2(entry, tmp_path):
    r = subprocess.run([sys.executable, str(entry), str(tmp_path / "no-such.html")],
                       capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 2, r.stdout + r.stderr
    assert "검사 대상 파일이 없다" in r.stderr


@pytest.mark.parametrize("entry", ENTRY_POINTS, ids=lambda p: str(p.relative_to(ROOT)))
def test_real_playwright_without_browsers_exits_2(entry, target, tmp_path):
    """
    실제 Playwright 에 빈 브라우저 경로를 주어 Chromium 이 없는 상태를 재현한다.
    위의 가짜 예외가 실제 메시지와 어긋나면 여기서 드러난다.
    """
    pytest.importorskip("playwright.sync_api")
    empty = tmp_path / "browsers"
    empty.mkdir()
    env = {**os.environ, "PLAYWRIGHT_BROWSERS_PATH": str(empty)}
    r = subprocess.run([sys.executable, str(entry), str(target)], capture_output=True, text=True,
                       encoding="utf-8", env=env, timeout=120)
    assert r.returncode == 2, r.stdout + r.stderr
    assert "-m playwright install chromium" in r.stderr
    assert "Traceback" not in r.stderr and "╔" not in r.stderr, r.stderr
