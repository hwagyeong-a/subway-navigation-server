"""Team B: KNN 기반 위치 추정기 (scikit-learn 채택).

Wi-Fi RSSI 벡터를 sklearn KNeighborsClassifier 로 분류해 현재 노드를 추정.
- K=3, weights='distance' (가까운 이웃에 가중치)
- 학습 데이터는 첫 호출 시 DB에서 한 번 읽어 모듈 캐시
- 팀 A의 _try_register_real_estimator 가 knn_estimate 함수를 자동 등록

새 스키마 대응 변경점:
- 학습 벡터가 list[int] → list[float] 로 바뀜 (rssi_mean DECIMAL)
- 입력 RSSI 도 float 처리 (scikit-learn 요구)
"""
from typing import List, Optional, Tuple

import numpy as np
from flask import current_app
from sklearn.neighbors import KNeighborsClassifier

from ..db.fingerprint import FingerprintRepository, RSSI_MISSING
from .locator import WifiSample
from .wifi_filter import filter_wifi_samples


K = 3

# 모듈 전역 캐시 - 첫 /locate 호출 시 채워짐
_bssid_order: Optional[List[str]] = None
_bssid_index: dict[str, int] = {}
_classifier: Optional[KNeighborsClassifier] = None
_loaded: bool = False


def _ensure_loaded() -> None:
    """첫 호출 시 DB에서 학습 데이터를 읽고 sklearn KNN 학습."""
    global _bssid_order, _bssid_index, _classifier, _loaded
    if _loaded:
        return

    repo = FingerprintRepository()
    _bssid_order = repo.list_bssid_order()
    _bssid_index = {b: i for i, b in enumerate(_bssid_order)}
    train_data = repo.load_training_set()

    if not train_data:
        # 학습 데이터가 없어도 로드 자체는 끝낸 것으로 간주.
        # 실제 predict 단계에서 RuntimeError 로 변환.
        _loaded = True
        return

    X = np.array([vec for _, vec in train_data], dtype=np.float32)
    y = np.array([node_id for node_id, _ in train_data])

    # n_neighbors 가 노드 수보다 크면 sklearn 이 에러 → 클램프
    k_actual = min(K, len(train_data))

    _classifier = KNeighborsClassifier(
        n_neighbors=k_actual,
        weights="distance",   # 가까운 이웃에 더 큰 가중치
        metric="euclidean",
    )
    _classifier.fit(X, y)
    _loaded = True

    current_app.logger.info(
        "KNN loaded: %d BSSIDs, %d nodes, K=%d",
        len(_bssid_order), len(train_data), k_actual,
    )


def _to_vector(samples: List[WifiSample]) -> np.ndarray:
    """입력 Wi-Fi 샘플을 BSSID 고정 순서 RSSI 벡터(numpy)로 변환."""
    measured: dict[str, float] = {}
    for s in samples:
        try:
            measured[s.bssid] = float(s.rssi)
        except (TypeError, ValueError):
            measured[s.bssid] = RSSI_MISSING

    vec = [measured.get(b, RSSI_MISSING) for b in _bssid_order or []]
    return np.array([vec], dtype=np.float32)  # shape (1, n_features)


def knn_estimate(samples: List[WifiSample]) -> str:
    """Wi-Fi 스캔으로 가장 가까운 노드(location)을 예측.

    Args:
        samples: 앱이 측정한 Wi-Fi 신호 목록.
                 앱에서 이미 5초×3샘플 평균 필터링을 거쳤다고 가정하지만
                 wifi_filter.filter_wifi_samples 로 한 번 더 안전망 적용.

    Returns:
        예측된 location 문자열 (예: "station_exit", "fare_gate").

    Raises:
        ValueError: 빈 샘플 입력 또는 필터링 후 빈 결과.
        RuntimeError: DB에 학습 데이터가 없음 / classifier 미초기화.
    """
    if not samples:
        raise ValueError("Empty Wi-Fi samples")

    # 안전망 필터 (RSSI<-90, 이동성 SSID 제거)
    filtered = filter_wifi_samples(samples)
    if not filtered:
        raise ValueError("All Wi-Fi samples filtered out (weak signal or mobile devices)")

    _ensure_loaded()

    if _classifier is None:
        raise RuntimeError(
            "KNN classifier not initialized. "
            "Ensure fingerprints table has training data."
        )

    query = _to_vector(filtered)
    pred = _classifier.predict(query)[0]
    return str(pred)


def knn_estimate_with_topk(samples: List[WifiSample], k: int = 3) -> List[Tuple[str, float]]:
    """디버깅/시연용: Top-K 후보 + 거리 반환.

    Returns:
        [(location, distance), ...] 가까운 순.
    """
    if not samples:
        raise ValueError("Empty Wi-Fi samples")
    filtered = filter_wifi_samples(samples)
    if not filtered:
        raise ValueError("All samples filtered out")

    _ensure_loaded()
    if _classifier is None:
        raise RuntimeError("KNN classifier not initialized")

    query = _to_vector(filtered)
    k_actual = min(k, _classifier.n_neighbors)
    distances, indices = _classifier.kneighbors(query, n_neighbors=k_actual)

    # _classifier.classes_ 는 정렬된 라벨 배열, indices 는 X_train 의 인덱스
    # → y_train 직접 접근이 필요한데 sklearn은 보관 안 함. 대신 _y_train 우회.
    y_train = _classifier._fit_X  # 학습 입력
    # _y 는 private 이므로 안전하게: 첫 호출 시 따로 저장하는 게 더 깔끔하지만
    # 여기서는 classes_ + predict 로 충분
    labels = [_classifier._y[i] for i in indices[0]]
    label_strs = [_classifier.classes_[label] for label in labels]

    return list(zip(label_strs, distances[0].tolist()))
