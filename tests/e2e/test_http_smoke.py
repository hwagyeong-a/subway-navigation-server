"""실 Flask 서버에 대한 HTTP smoke test.

Flask test client 가 아닌 `requests` 로 실제 네트워크 호출을 검증한다.
"""
import requests


def test_health(live_server):
    r = requests.get(f"{live_server}/health", timeout=5)
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_direction_real_data(live_server):
    r = requests.post(
        f"{live_server}/direction",
        json={"from": "station_exit", "to": "floor1_hall"},
        timeout=5,
    )
    assert r.status_code == 200
    body = r.json()
    assert body["angle"] == 268
    assert body["cardinal"] == "W"
    assert body["clock"] == 9


def test_direction_cardinal_field(live_server):
    r = requests.post(
        f"{live_server}/direction",
        json={"from": "floor1_hall", "to": "station_exit"},
        timeout=5,
    )
    assert r.status_code == 200
    assert r.json()["cardinal"] == "E"


def test_direction_invalid_node(live_server):
    r = requests.post(
        f"{live_server}/direction",
        json={"from": "station_exit", "to": "ghost"},
        timeout=5,
    )
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "INVALID_NODE"


def test_route_real_data_full(live_server):
    r = requests.post(
        f"{live_server}/route",
        json={"from": "station_exit", "to": "down_platform"},
        timeout=5,
    )
    assert r.status_code == 200
    body = r.json()
    assert body["path"][0]["node"] == "station_exit"
    assert body["path"][-1]["node"] == "down_platform"
    # 중간 노드들 모두 edge_type 가지고 있어야 함
    for step in body["path"][:-1]:
        assert step["edge_to_next"] in ("flat", "stairs", "branch")
    # 계단 구간이 경로 어디엔가 있어야 함 (ground → B1 이동 위해)
    assert any(s["edge_to_next"] == "stairs" for s in body["path"][:-1])


def test_route_to_up_platform(live_server):
    r = requests.post(
        f"{live_server}/route",
        json={"from": "station_exit", "to": "up_platform"},
        timeout=5,
    )
    assert r.status_code == 200
    path = r.json()["path"]
    assert path[0]["node"] == "station_exit"
    assert path[-1]["node"] == "up_platform"


def test_route_invalid_returns_envelope(live_server):
    r = requests.post(
        f"{live_server}/route",
        json={"from": "ghost", "to": "down_platform"},
        timeout=5,
    )
    assert r.status_code == 400
    body = r.json()
    # docs §5.5 envelope 형식 검증
    assert "error" in body
    assert "code" in body["error"]
    assert "message" in body["error"]


def test_swagger_apispec_json(live_server):
    r = requests.get(f"{live_server}/apispec_1.json", timeout=5)
    assert r.status_code == 200
    paths = r.json().get("paths", {})
    for expected in ("/direction", "/route", "/locate", "/health"):
        assert expected in paths


def test_swagger_apidocs_html(live_server):
    r = requests.get(f"{live_server}/apidocs/", timeout=5)
    assert r.status_code == 200
    assert "text/html" in r.headers.get("Content-Type", "")
    # Swagger UI 가 들어있는지 마커 검사
    body_lower = r.text.lower()
    assert "swagger" in body_lower or "openapi" in body_lower
