"""Team B: fingerprint 저장소 (새 스키마 대응).

새 DB 스키마는 `fingerprints` 테이블의 컬럼이 mac, rssi_mean 으로
바뀌었지만, KNN/locator 측 코드가 기존 이름(bssid, rssi)을 그대로
쓰도록 SQL alias 로 매핑한다.

[2026-05-28 개선] 측위 정확도 향상
- 기존 load_training_set(): fingerprints(노드당 평균 1개)로 학습
  → 11노드 = 학습 11개. KNN 이 노드 경계에서 오인식하기 쉬움.
- 추가 load_training_set_from_raw(): raw_measurements 의 개별 스캔
  ((location, sample_id) 단위)으로 학습 → 노드당 측정 횟수만큼(예: 10개).
  KNN 이 노드별 신호 '분포'를 학습해 실시간 측위가 안정적.
"""
from .connection import get_connection


# AP가 측정되지 않았음을 나타내는 sentinel 값.
RSSI_MISSING = -100.0


class FingerprintRepository:
    """Wi-Fi fingerprint 학습 데이터 읽기 전용 접근."""

    def list_bssid_order(self) -> list[str]:
        """모든 고유 MAC 주소를 알파벳 오름차순으로 반환.

        raw_measurements 와 fingerprints 양쪽 mac 을 합집합으로 모은다.
        (학습을 raw 로 하더라도 bssid_order 는 동일 기준이어야 하므로)
        """
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute(
                "SELECT DISTINCT mac AS bssid "
                "FROM fingerprints "
                "WHERE mac IS NOT NULL "
                "ORDER BY mac ASC"
            )
            rows = cur.fetchall()
        return [r[0] for r in rows]

    def load_training_set(self) -> list[tuple[str, list[float]]]:
        """[기존/평균] (location, rssi_vector) 쌍을 모든 노드에 대해 반환.

        fingerprints 테이블의 노드별 평균값 → 노드당 벡터 1개.
        호환성 위해 유지. 기본 학습은 load_training_set_from_raw 권장.
        """
        bssid_order = self.list_bssid_order()
        bssid_index = {b: i for i, b in enumerate(bssid_order)}
        n_features = len(bssid_order)

        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute(
                "SELECT location  AS node_id, "
                "       mac       AS bssid, "
                "       rssi_mean AS rssi "
                "FROM fingerprints "
                "WHERE location IS NOT NULL AND mac IS NOT NULL"
            )
            rows = cur.fetchall()

        node_vectors: dict[str, list[float]] = {}
        for node_id, bssid, rssi in rows:
            if bssid not in bssid_index:
                continue
            vec = node_vectors.get(node_id)
            if vec is None:
                vec = [RSSI_MISSING] * n_features
                node_vectors[node_id] = vec
            vec[bssid_index[bssid]] = float(rssi)

        return list(node_vectors.items())

    def load_training_set_from_raw(self) -> list[tuple[str, list[float]]]:
        """[개선/개별] raw_measurements 의 개별 스캔을 학습 샘플로 반환.

        (location, sample_id) 단위로 하나의 스캔 = 하나의 학습 벡터.
        노드당 측정 횟수만큼 샘플이 생겨(예: 10회 측정 → 10개), KNN 이
        노드별 신호 분포를 학습한다. 실시간 측위 안정성이 향상된다.

        반환: [(location, rssi_vector), ...]  — 노드당 여러 개
        bssid_order 는 list_bssid_order() 와 동일 기준(fingerprints 기반)을
        사용해, 추론 시 normalize_wifi 와 차원이 정확히 일치한다.
        """
        bssid_order = self.list_bssid_order()
        bssid_index = {b: i for i, b in enumerate(bssid_order)}
        n_features = len(bssid_order)

        if n_features == 0:
            return []

        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute(
                "SELECT location AS node_id, "
                "       sample_id, "
                "       mac, "
                "       rssi_dBm AS rssi "
                "FROM raw_measurements "
                "WHERE location IS NOT NULL AND mac IS NOT NULL"
            )
            rows = cur.fetchall()

        # (location, sample_id) 단위로 벡터 구성
        scan_vectors: dict[tuple, list[float]] = {}
        scan_node: dict[tuple, str] = {}
        for node_id, sample_id, mac, rssi in rows:
            if mac not in bssid_index:
                continue  # fingerprints 에 없는 mac 은 무시 (차원 일치 보장)
            key = (node_id, sample_id)
            vec = scan_vectors.get(key)
            if vec is None:
                vec = [RSSI_MISSING] * n_features
                scan_vectors[key] = vec
                scan_node[key] = node_id
            vec[bssid_index[mac]] = float(rssi)

        return [(scan_node[key], vec) for key, vec in scan_vectors.items()]