"""Team B: fingerprint 저장소 (새 스키마 대응).

새 DB 스키마는 `fingerprints` 테이블의 컬럼이 mac, rssi_mean 으로
바뀌었지만, KNN/locator 측 코드가 기존 이름(bssid, rssi)을 그대로
쓰도록 SQL alias 로 매핑한다.
"""
from .connection import get_connection


# AP가 측정되지 않았음을 나타내는 sentinel 값.
RSSI_MISSING = -100.0


class FingerprintRepository:
    """Wi-Fi fingerprint 학습 데이터 읽기 전용 접근."""

    def list_bssid_order(self) -> list[str]:
        """모든 고유 MAC 주소를 알파벳 오름차순으로 반환."""
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
        """(location, rssi_vector) 쌍을 모든 노드에 대해 반환."""
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
