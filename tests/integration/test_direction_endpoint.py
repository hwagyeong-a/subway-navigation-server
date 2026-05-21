def test_direction_happy_path(client):
    # station_exit → floor1_hall : 268° W 9시
    res = client.post("/direction", json={"from": "station_exit", "to": "floor1_hall"})
    assert res.status_code == 200
    assert res.get_json() == {"angle": 268, "cardinal": "W", "clock": 9}


def test_direction_returns_three_fields(client):
    res = client.post("/direction", json={"from": "floor1_hall", "to": "fare_gate"})
    body = res.get_json()
    assert set(body.keys()) == {"angle", "cardinal", "clock"}


def test_direction_invalid_from_node_returns_400(client):
    res = client.post("/direction", json={"from": "ghost", "to": "floor1_hall"})
    assert res.status_code == 400
    assert res.get_json()["error"]["code"] == "INVALID_NODE"


def test_direction_invalid_to_node_returns_400(client):
    res = client.post("/direction", json={"from": "station_exit", "to": "ghost"})
    assert res.status_code == 400
    assert res.get_json()["error"]["code"] == "INVALID_NODE"


def test_direction_not_connected_returns_400(client):
    # station_exit 와 b1_stairs 는 fixture 에서 직접 연결되지 않음
    res = client.post("/direction", json={"from": "station_exit", "to": "b1_stairs"})
    assert res.status_code == 400
    assert res.get_json()["error"]["code"] == "NOT_CONNECTED"


def test_direction_missing_field_returns_400(client):
    res = client.post("/direction", json={"from": "station_exit"})
    assert res.status_code == 400
    assert res.get_json()["error"]["code"] == "INVALID_PAYLOAD"


def test_direction_non_json_body_returns_400(client):
    res = client.post(
        "/direction", data="not-json", content_type="application/json"
    )
    assert res.status_code == 400
    assert res.get_json()["error"]["code"] == "INVALID_PAYLOAD"
