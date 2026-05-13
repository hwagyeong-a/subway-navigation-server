"""Team B: KNN 기반 위치 추정기.

Wi-Fi RSSI 패턴 비교(K=3 다수결)로 현재 노드를 추정.
학습 데이터는 첫 호출 시 DB에서 한 번 읽어 모듈 캐시.
팀 A의 create_app()이 knn_estimate를 자동 등록한다.
"""
from collections import Counter
from math import sqrt
from typing import List, Optional, Tuple

from flask import current_app

from ..db.fingerprint import FingerprintRepository, RSSI_MISSING
from .locator import WifiSample


K = 3

# 모듈 전역 캐시 — 첫 /locate 호출 시 채워짐.
_bssid_order: Optional[List[str]] = None
_bssid_index: dict[str, int] = {}
_train_data: List[Tuple[str, List[int]]] = []
_loaded: bool = False


def _ensure_loaded() -> None:
    """첫 호출 시 DB에서 학습 데이터를 읽어 캐시."""
    global _bssid_order, _bssid_index, _train_data, _loaded
    if _loaded:
        return

    repo = FingerprintRepository()
    _bssid_order = repo.list_bssid_order()
    _bssid_index = {b: i for i, b in enumerate(_bssid_order)}
    _train_data = repo.load_training_set()
    _loaded = True

    current_app.logger.info(
        "KNN loaded: %d BSSIDs, %d nodes",
        len(_bssid_order),
        len(_train_data),
    )


def _to_vector(samples: List[WifiSample]) -> List[int]:
    """입력 Wi-Fi 샘플을 BSSID 고정 순서 RSSI 벡터로 변환."""
    measured: dict[str, int] = {}
    for s in samples:
        try:
            measured[s.bssid] = int(s.rssi)
        except (TypeError, ValueError):
            measured[s.bssid] = RSSI_MISSING

    return [measured.get(b, RSSI_MISSING) for b in _bssid_order or []]


def _euclidean(v1: List[int], v2: List[int]) -> float:
    """두 RSSI 벡터 간 유클리드 거리."""
    n = min(len(v1), len(v2))
    return sqrt(sum((v1[i] - v2[i]) ** 2 for i in range(n)))


def knn_estimate(samples: List[WifiSample]) -> str:
    """Wi-Fi 스캔으로 가장 가까운 노드 ID 예측.

    Raises:
        ValueError: 빈 샘플 입력.
        RuntimeError: DB에 학습 데이터가 없음.
    """
    if not samples:
        raise ValueError("Empty Wi-Fi samples")

    _ensure_loaded()

    if not _train_data:
        raise RuntimeError(
            "No fingerprint training data in DB. "
            "Run data collection before calling /locate."
        )

    query = _to_vector(samples)

    distances: List[Tuple[float, str]] = [
        (_euclidean(query, vec), node_id)
        for node_id, vec in _train_data
        if vec
    ]
    if not distances:
        raise RuntimeError("Training data has no usable vectors")

    distances.sort(key=lambda t: t[0])
    top_k = distances[:K]

    votes = Counter(node_id for _, node_id in top_k)
    max_count = max(votes.values())
    candidates = [n for n, c in votes.items() if c == max_count]

    if len(candidates) == 1:
        return candidates[0]

    # 동률: top_k 내 후보별 거리 합 최소
    sum_dist = {n: 0.0 for n in candidates}
    for dist, node_id in top_k:
        if node_id in sum_dist:
            sum_dist[node_id] += dist
    return min(sum_dist.items(), key=lambda t: t[1])[0]
