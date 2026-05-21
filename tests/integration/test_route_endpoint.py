def test_route_happy_path(client):
    res = client.post("/route", json={"from": "station_exit", "to": "b1_stairs"})
    assert res.status_code == 200
    body = res.get_json()
    assert isinstance(body["path"], list)
    assert len(body["path"]) >= 3


def test_route_path_starts_and_ends_correctly(client):
    res = client.post("/route", json={"from": "station_exit", "to": "b1_stairs"})
    path = res.get_json()["path"]
    assert path[0]["node"] == "station_exit"
    assert path[-1]["node"] == "b1_stairs"


def test_route_includes_edge_type(client):
    res = client.post("/route", json={"from": "station_exit", "to": "b1_stairs"})
    path = res.get_json()["path"]
    # 마지막 노드를 제외한 모든 노드는 edge_to_next 가 있어야 함
    for step in path[:-1]:
        assert step["edge_to_next"] in ("flat", "stairs", "branch")


def test_route_path_terminus_has_null_edge_to_next(client):
    res = client.post("/route", json={"from": "station_exit", "to": "b1_stairs"})
    path = res.get_json()["path"]
    assert path[-1]["edge_to_next"] is None


def test_route_path_includes_floor_metadata(client):
    res = client.post("/route", json={"from": "station_exit", "to": "b1_stairs"})
    for step in res.get_json()["path"]:
        assert "floor" in step
        assert "zone" in step


def test_route_short_path(client):
    res = client.post("/route", json={"from": "station_exit", "to": "floor1_hall"})
    path = res.get_json()["path"]
    assert len(path) == 2


def test_route_same_node(client):
    res = client.post("/route", json={"from": "fare_gate", "to": "fare_gate"})
    body = res.get_json()
    assert len(body["path"]) == 1
    assert body["path"][0]["node"] == "fare_gate"
    assert body["path"][0]["edge_to_next"] is None


def test_route_invalid_node_returns_400(client):
    res = client.post("/route", json={"from": "station_exit", "to": "ghost"})
    assert res.status_code == 400
    assert res.get_json()["error"]["code"] == "INVALID_NODE"


def test_route_no_route_returns_404(client):
    # isolated 노드는 fixture 에서 어디에도 연결 안 됨
    res = client.post("/route", json={"from": "station_exit", "to": "isolated"})
    assert res.status_code == 404
    assert res.get_json()["error"]["code"] == "NO_ROUTE"


def test_route_missing_field_returns_400(client):
    res = client.post("/route", json={"from": "station_exit"})
    assert res.status_code == 400
    assert res.get_json()["error"]["code"] == "INVALID_PAYLOAD"


def test_route_no_danger_destination_error(client):
    # 어떤 입력에도 DANGER_DESTINATION 코드 나오지 않음 (회귀 방지)
    for to_node in ["floor1_hall", "fare_gate", "stairs_mid", "b1_stairs"]:
        res = client.post("/route", json={"from": "station_exit", "to": to_node})
        if "error" in (res.get_json() or {}):
            assert res.get_json()["error"]["code"] != "DANGER_DESTINATION"
