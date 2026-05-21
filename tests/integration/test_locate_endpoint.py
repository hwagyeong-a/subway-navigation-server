from subway_server.core import locator


def test_locate_returns_estimator_result(client, fake_estimator):
    fake_estimator("fare_gate")
    res = client.post(
        "/locate",
        json={"wifi": [{"bssid": "aa:bb:cc:dd:ee:ff", "rssi": -65}]},
    )
    assert res.status_code == 200
    assert res.get_json() == {"node": "fare_gate"}


def test_locate_empty_wifi_returns_400(client):
    res = client.post("/locate", json={"wifi": []})
    assert res.status_code == 400
    assert res.get_json()["error"]["code"] == "EMPTY_WIFI"


def test_locate_missing_wifi_returns_400(client):
    res = client.post("/locate", json={})
    assert res.status_code == 400
    assert res.get_json()["error"]["code"] == "INVALID_PAYLOAD"


def test_locate_bad_wifi_item_returns_400(client):
    res = client.post(
        "/locate", json={"wifi": [{"bssid": "aa", "rssi": "not-int"}]}
    )
    assert res.status_code == 400
    assert res.get_json()["error"]["code"] == "INVALID_PAYLOAD"


def test_locate_estimator_not_registered_returns_500(client):
    # Default stub raises NotImplementedError → mapped to KNN_ERROR.
    res = client.post(
        "/locate",
        json={"wifi": [{"bssid": "aa:bb:cc:dd:ee:ff", "rssi": -65}]},
    )
    assert res.status_code == 500
    assert res.get_json()["error"]["code"] == "KNN_ERROR"


def test_locate_estimator_failure_returns_500(client):
    def boom(samples):
        raise RuntimeError("internal explosion")

    locator.register_estimator(boom)
    res = client.post(
        "/locate",
        json={"wifi": [{"bssid": "aa:bb:cc:dd:ee:ff", "rssi": -65}]},
    )
    assert res.status_code == 500
    assert res.get_json()["error"]["code"] == "KNN_ERROR"


def test_locate_passes_samples_to_estimator(client):
    received = {}

    def capture(samples):
        received["samples"] = samples
        return "X"

    locator.register_estimator(capture)
    client.post(
        "/locate",
        json={
            "wifi": [
                {"bssid": "aa", "rssi": -50},
                {"bssid": "bb", "rssi": -70},
            ]
        },
    )
    samples = received["samples"]
    assert len(samples) == 2
    assert samples[0].bssid == "aa"
    assert samples[0].rssi == -50
