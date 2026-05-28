"""Team B: KNN 기반 위치 추정기 (마스킹 거리 채택).

CLAUDE.md 'Wi-Fi pipeline split' 준수:
- Team A 의 core/wifi.py::normalize_wifi 는 학습 벡터 정렬에 활용
- B 의 knn_estimate 가 FingerprintRepository(평균 centroid) + 마스킹 거리 사용

[2026-05-28 개선] 마스킹 거리(measured-only distance)
- 문제: 지하철역은 사람/기둥에 막혀 AP 가 자주 누락(dropout)된다.
  기존 방식은 누락 AP 를 -100(아주 멀다)으로 채워 거리를 계산했는데,
  이는 '신호 약함'이 아니라 '측정 안 됨'을 멀다고 왜곡 -> 오인식.
- 개선: 쿼리에서 '측정된 AP 차원'으로만 거리를 계산(누락 AP 는 제외).
  학습 데이터는 기존 평균(centroid) 방식 그대로 사용한다.
- 검증(method_compare.py, dropout 환경):
    심한 혼잡(출퇴근)  기존 21% -> 마스킹 87.5%
    극심(사람 가득)    기존 9.9% -> 마스킹 73.2%
"""
from typing import List, Optional

import numpy as np
from flask import current_app

from ..db.fingerprint import FingerprintRepository
from .locator import WifiSample
from .wifi_filter import filter_wifi_samples


_DEFAULT_K = 5

_bssid_order: Optional[List[str]] = None
_bssid_index: Optional[dict] = None
_train_X: Optional[np.ndarray] = None   # (n_samples, n_features) 평균 centroid
_train_y: Optional[np.ndarray] = None   # (n_samples,) location 라벨
_loaded: bool = False


def _ensure_loaded() -> None:
    """첫 호출 시 DB 에서 노드별 평균 centroid 로드."""
    global _bssid_order, _bssid_index, _train_X, _train_y, _loaded
    if _loaded:
        return

    repo = FingerprintRepository()
    _bssid_order = repo.list_bssid_order()
    _bssid_index = {b: i for i, b in enumerate(_bssid_order)}

    # 노드당 평균 벡터 (안정적인 centroid). 마스킹 거리로 dropout 에 대응.
    train_data = repo.load_training_set()
    if not train_data:
        _loaded = True
        return

    _train_X = np.array([vec for _, vec in train_data], dtype=np.float32)
    _train_y = np.array([node_id for node_id, _ in train_data])
    _loaded = True

    current_app.logger.info(
        "KNN(masked) loaded: %d BSSIDs, %d nodes",
        len(_bssid_order), len(train_data),
    )


def knn_estimate(samples: List[WifiSample]) -> str:
    """Wi-Fi 스캔으로 가장 가까운 노드(location)를 예측 (마스킹 거리)."""
    if not samples:
        raise ValueError("Empty Wi-Fi samples")

    filtered = filter_wifi_samples(samples)
    if not filtered:
        raise ValueError("All Wi-Fi samples below RSSI threshold")

    _ensure_loaded()

    if _train_X is None or len(_train_X) == 0:
        raise RuntimeError(
            "KNN classifier not initialized — "
            "no fingerprint training data in DB"
        )

    # 측정된 AP 중 학습 벡터에 존재하는 차원만 추출
    measured_idx = []
    measured_rssi = []
    for s in filtered:
        idx = _bssid_index.get(s.bssid)
        if idx is not None:
            measured_idx.append(idx)
            measured_rssi.append(s.rssi)

    if not measured_idx:
        raise ValueError("No measured AP overlaps with fingerprint BSSIDs")

    q = np.array(measured_rssi, dtype=np.float32)
    # 측정된 차원만으로 euclidean 거리 (누락 AP 는 거리에서 제외 = 마스킹)
    X_sub = _train_X[:, measured_idx]
    dists = np.sqrt(np.sum((X_sub - q) ** 2, axis=1))

    k_cfg = current_app.config.get("KNN_K", _DEFAULT_K)
    k = min(k_cfg, len(dists))
    nearest = np.argsort(dists)[:k]

    # 거리 가중 투표
    votes: dict = {}
    for idx in nearest:
        label = _train_y[idx]
        votes[label] = votes.get(label, 0.0) + 1.0 / (float(dists[idx]) + 1e-6)

    return str(max(votes, key=votes.get))