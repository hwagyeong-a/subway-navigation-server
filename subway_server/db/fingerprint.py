"""Team B: fingerprint 저장소 (새 스키마 대응).

새 DB 스키마는 `fingerprints` 테이블의 컬럼이 mac, rssi_mean 으로
바뀌었지만, KNN/locator 측 코드가 기존 이름(bssid, rssi)을 그대로
쓰도록 SQL alias 로 매핑한다.

팀 A가 정의한 계약 (유지):
    list_bssid_order()  -> list[str]
    load_training_set() -> list[tuple[str, list[float]]]

새 스키마(2026-05-15 갱신):
    fingerprints(
        location VARCHAR(64),  -- node_id 역할
        mac      VARCHAR(17),  -- bssid 역할
        rssi_mean DECIMAL(6,2) -- 이미 평균이 계산되어 들어옴
        ...
    )
"""
from .connection import get_connection


# AP가 측정되지 않았음을 나타내는 sentinel 값.
# knn.py 입력 처리 쪽과 반드시 동일한 값을 사용해야 함.
RSSI_MISSING = -100.0


class FingerprintRepository:
    """Wi-Fi fingerprint 학습 데이터 읽기 전용 접근.

    Connection은 메서드 호출 시 get_connection()으로 가져온다.
    인자 없이 인스턴스화하면 된다: repo = FingerprintRepository()
    """

    def list_bssid_order(self) -> list[str]:
        """모든 고유 MAC 주소를 알파벳 오름차순으로 반환.

        반환 이름은 'bssid' 의미를 유지 (KNN 코드 호환).
        이 순서가 학습/예측 벡터의 차원 인덱스를 정의한다.
        """
        conn = get_connection()
        with conn.cursor() as cur:
            # mac → bssid 의미 alias
            cur.execute(
                "SELECT DISTINCT mac AS bssid "
                "FROM fingerprints "
                "WHERE mac IS NOT NULL "
                "ORDER BY mac ASC"
            )
            rows = cur.fetchall()
        return [r[0] for r in rows]

    def load_training_set(self) -> list[tuple[str, list[float]]]:
        """(location, rssi_vector) 쌍을 모든 노드에 대해 반환.

        새 스키마는 이미 rssi_mean 으로 통계가 계산되어 있으므로
        SQL AVG() 가 필요 없다. 그대로 가져와 벡터에 채운다.

        rssi_vector 길이 == len(list_bssid_order()) 와 동일 순서.
        해당 노드에서 측정되지 않은 AP는 RSSI_MISSING(-100.0)로 채움.

        반환 타입의 두번째 요소가 list[int] → list[float] 로 바뀐 점
        주의. rssi_mean 이 DECIMAL 이라 자연수 변환은 정보 손실이며,
        scikit-learn KNN 도 float 을 요구한다.
        """
        bssid_order = self.list_bssid_order()
        bssid_index = {b: i for i, b in enumerate(bssid_order)}
        n_features = len(bssid_order)

        conn = get_connection()
        with conn.cursor() as cur:
            # location → node_id, mac → bssid, rssi_mean → rssi 로 alias
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
