"""Playwright 로 Swagger UI 실제 렌더링·인터랙션 검증.

발표 자료용 스크린샷도 함께 생성.
"""
from pathlib import Path

import pytest
from playwright.sync_api import Page, expect


SCREENSHOT_DIR = Path(__file__).parent / "screenshots"
SCREENSHOT_DIR.mkdir(exist_ok=True)


def test_apidocs_renders(page: Page, live_server: str):
    page.goto(f"{live_server}/apidocs/")
    # Flasgger 가 만든 Swagger UI 페이지 — Powered by Flasgger 마커 확인
    expect(page.locator("body")).to_contain_text("Flasgger")
    # 4개 endpoint 가 표시되어야 함
    expect(page.locator(".opblock-summary-path")).to_have_count(4)


def test_endpoints_visible(page: Page, live_server: str):
    page.goto(f"{live_server}/apidocs/")
    paths = page.locator(".opblock-summary-path")
    # Swagger UI 가 path 앞에 zero-width space 를 넣는 경우가 있어 부분 매치로 검증
    path_texts = [paths.nth(i).inner_text() for i in range(paths.count())]
    for expected in ("/locate", "/route", "/direction", "/health"):
        assert any(expected in t for t in path_texts), (
            f"Missing endpoint in Swagger UI: {expected!r}, found: {path_texts!r}"
        )


def test_screenshot_for_demo(page: Page, live_server: str):
    """5/22 중간 미팅 발표 자료용 스크린샷 캡쳐."""
    page.goto(f"{live_server}/apidocs/")
    # 페이지가 안정될 때까지 잠시 대기
    page.wait_for_load_state("networkidle")
    out = SCREENSHOT_DIR / "swagger_overview.png"
    page.screenshot(path=str(out), full_page=True)
    assert out.exists()


def test_screenshot_route_section(page: Page, live_server: str):
    """`/route` 영역 펼친 상태의 스크린샷."""
    page.goto(f"{live_server}/apidocs/")
    page.wait_for_load_state("networkidle")
    # 첫 번째 path /direction (POST) 또는 /route 를 펼치기
    page.locator(".opblock-summary-path", has_text="/route").first.click()
    out = SCREENSHOT_DIR / "swagger_route_expanded.png"
    page.screenshot(path=str(out), full_page=True)
    assert out.exists()
