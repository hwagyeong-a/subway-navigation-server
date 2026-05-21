"""Team B: Wi-Fi 샘플 안전망 필터.

앱에서 이미 *5초×3샘플 평균 + 1차 필터링* 을 거쳐 보낸다고 가정하지만,
서버에서도 한 번 더 필터링해 잘못된 입력을 막는다.

⚠️ 현재 상태 (2026-05-15):
   WifiSample 에 ssid 필드가 아직 없어 SSID 필터는 자동 스킵됨
   (getattr 로 안전 처리). 추후 팀 A 와 합의되어 ssid 가 추가되면
   별도 코드 변경 없이 즉시 동작 시작.
"""
import re
from typing import List

from .locator import WifiSample


MIN_RSSI_DBM = -90

_MOBILE_PATTERNS = [
    re.compile(r"\[dryer\]", re.IGNORECASE),
    re.compile(r"iphone", re.IGNORECASE),
    re.compile(r"android", re.IGNORECASE),
    re.compile(r"galaxy", re.IGNORECASE),
    re.compile(r"airpods", re.IGNORECASE),
    re.compile(r"buds", re.IGNORECASE),
    re.compile(r"^direct-", re.IGNORECASE),
    re.compile(r"hotspot", re.IGNORECASE),
]


def is_mobile_ssid(ssid: str | None) -> bool:
    """SSID 가 이동성 기기로 의심되는지 판단."""
    if not ssid:
        return False
    return any(p.search(ssid) for p in _MOBILE_PATTERNS)


def filter_wifi_samples(samples: List[WifiSample]) -> List[WifiSample]:
    """약한 신호 + 이동성 기기 제거."""
    result = []
    for s in samples:
        try:
            rssi = float(s.rssi)
        except (TypeError, ValueError):
            continue
        if rssi < MIN_RSSI_DBM:
            continue
        ssid = getattr(s, "ssid", None)
        if ssid and is_mobile_ssid(ssid):
            continue
        result.append(s)
    return result