"""서버측 Wi-Fi 안전망 필터 검증.

WifiSample 에 ssid 필드가 추가되면서 이동성 기기 SSID 필터가 활성화됨을 확인.
(filter_wifi_samples 는 KNN 모듈 knn_estimate 내부에서 호출됨)
"""
from subway_server.core.locator import WifiSample
from subway_server.core.wifi_filter import filter_wifi_samples, is_mobile_ssid


def test_filters_weak_rssi():
    samples = [WifiSample("aa", -50.0), WifiSample("bb", -95.0)]
    result = filter_wifi_samples(samples)
    assert [s.bssid for s in result] == ["aa"]


def test_filters_mobile_ssid_iphone():
    samples = [
        WifiSample("aa", -50.0, "Korail_WiFi_Free"),
        WifiSample("bb", -50.0, "iPhone"),
    ]
    result = filter_wifi_samples(samples)
    bssids = [s.bssid for s in result]
    assert "aa" in bssids
    assert "bb" not in bssids


def test_filters_mobile_ssid_various():
    mobile = [
        WifiSample("a", -40.0, "[dryer]"),
        WifiSample("b", -40.0, "Galaxy S24"),
        WifiSample("c", -40.0, "someones-airpods"),
        WifiSample("d", -40.0, "DIRECT-xy-Printer"),
    ]
    assert filter_wifi_samples(mobile) == []


def test_keeps_when_ssid_none():
    # ssid 없으면 (예전 호환) RSSI 만으로 판단, 통과
    samples = [WifiSample("aa", -50.0)]
    assert len(filter_wifi_samples(samples)) == 1


def test_is_mobile_ssid():
    assert is_mobile_ssid("iPhone")
    assert is_mobile_ssid("[dryer]")
    assert is_mobile_ssid("MY-GALAXY")
    assert not is_mobile_ssid("Korail_WiFi_Free")
    assert not is_mobile_ssid("Public WiFi Free")
    assert not is_mobile_ssid(None)
