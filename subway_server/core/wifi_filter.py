"""Team B: Wi-Fi 샘플 안전망 필터.

앱에서 이미 *5초×3샘플 평균 + 1차 필터링* 을 거쳐 보낸다고 가정하지만,
서버에서도 한 번 더 필터링해 잘못된 입력을 막는다.

필터 규칙 (앱과 동일):
1. RSSI ≥ -90 dBm
2. 이동성 기기 SSID 제외 (iPhone, [dryer], Android 등)
"""
import re
from typing import List

from .locator import WifiSample


# RSSI 하한 (이 값 미만은 신호가 너무 약해 신뢰 불가)
MIN_RSSI_DBM = -90

# 이동성 기기 SSID 패턴 (대소문자 무시)
# 패턴 추가 시 docs/09-결정사항.md §9.3 D-XX 에 기록할 것
_MOBILE_PATTERNS = [
    re.compile(r"\[dryer\]", re.IGNORECASE),    # 삼성 일부 가전/IoT
    re.compile(r"iphone", re.IGNORECASE),
    re.compile(r"android", re.IGNORECASE),
    re.compile(r"galaxy", re.IGNORECASE),
    re.compile(r"airpods", re.IGNORECASE),
    re.compile(r"buds", re.IGNORECASE),         # 갤럭시 버즈
    re.compile(r"^direct-", re.IGNORECASE),     # Wi-Fi Direct (프린터 등)
    re.compile(r"hotspot", re.IGNORECASE),
]


def is_mobile_ssid(ssid: str | None) -> bool:
    """SSID가 이동성 기기로 의심되는지 판단."""
    if not ssid:
        return False
    return any(p.search(ssid) for p in _MOBILE_PATTERNS)


def filter_wifi_samples(samples: List[WifiSample]) -> List[WifiSample]:
    """약한 신호 + 이동성 기기 제거.

    WifiSample 에 ssid 필드가 없으면 SSID 필터는 건너뛴다.
    필드 존재 여부는 hasattr 로 안전 체크 (팀 A 인터페이스 변화 대비).
    """
    result = []
    for s in samples:
        try:
            rssi = float(s.rssi)
        except (TypeError, ValueError):
            continue

        # 1) RSSI 임계
        if rssi < MIN_RSSI_DBM:
            continue

        # 2) 이동성 SSID
        ssid = getattr(s, "ssid", None)
        if ssid and is_mobile_ssid(ssid):
            continue

        result.append(s)

    return result
