"""Team B: fingerprint 저장소.

팀 A가 정의한 계약을 구현:
    list_bssid_order()  -> list[str]
    load_training_set() -> list[tuple[str, list[int]]]

스키마: fingerprint(id PK, node_id, bssid VARCHAR(17), rssi INT)
"""
from .connection import get_connection


# AP가 측정되지 않았음을 나타내는 sentinel 값.
# knn.py 입력 처리 쪽과 반드시 동일한 값을 사용해야 함.
RSSI_MISSING = -100


class FingerprintRepository:
    """Wi-Fi fingerprint 학습 데이터 읽기 전용 접근.

    Connection은 메서드 호출 시 get_connection()으로 가져온다.
    인자 없이 인스턴스화하면 된다: repo = FingerprintRepository()
    """

    def list_bssid_order(self) -> list[str]:
        """모든 고유 BSSID를 알파벳 오름차순으로 반환.

        이 순서가 학습/예측 벡터의 차원 인덱스를 정의한다.
        순서가 호출 간 바뀌면 KNN 거리 계산이 의미를 잃는다.
        """
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute(
                "SELECT DISTINCT bssid "
                "FROM fingerprint "
                "WHERE bssid IS NOT NULL "
                "ORDER BY bssid ASC"
            )
            rows = cur.fetchall()
        return [r[0] for r in rows]

    def load_training_set(self) -> list[tuple[str, list[int]]]:
        """(node_id, rssi_vector) 쌍을 모든 노드에 대해 반환.

        rssi_vector 길이는 list_bssid_order()와 동일하며 동일 순서.
        해당 노드에서 측정되지 않은 AP는 RSSI_MISSING(-100)로 채움.
        같은 (node_id, bssid)의 다중 샘플은 AVG로 평균 처리.
        """
        bssid_order = self.list_bssid_order()
        bssid_index = {b: i for i, b in enumerate(bssid_order)}
        n_features = len(bssid_order)

        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute(
                "SELECT node_id, bssid, AVG(rssi) "
                "FROM fingerprint "
                "WHERE node_id IS NOT NULL AND bssid IS NOT NULL "
                "GROUP BY node_id, bssid"
            )
            rows = cur.fetchall()

        node_vectors: dict[str, list[int]] = {}
        for node_id, bssid, avg_rssi in rows:
            if bssid not in bssid_index:
                continue
            vec = node_vectors.get(node_id)
            if vec is None:
                vec = [RSSI_MISSING] * n_features
                node_vectors[node_id] = vec
            vec[bssid_index[bssid]] = int(round(float(avg_rssi)))

        return list(node_vectors.items())
