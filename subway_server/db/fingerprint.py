"""Team B: fingerprint repository.

Contract (defined by Team A — do not break):
    list_bssid_order() -> list[str]
    load_training_set() -> list[tuple[str, list[int]]]

Schema assumption (see scripts/schema.sql):
    fingerprint(id PK, node_id VARCHAR, bssid VARCHAR(17), rssi INT)
"""
from .connection import get_connection


# RSSI sentinel for "AP not seen at this node". Matches the value used
# on the input side in knn.py — both sides MUST agree.
RSSI_MISSING = -100


class FingerprintRepository:
    """Read-only access to Wi-Fi fingerprint training data.

    Connection is fetched lazily per call via get_connection(), which
    returns the request-scoped connection. Safe to instantiate without
    arguments.
    """

    def list_bssid_order(self) -> list[str]:
        """Return all distinct BSSIDs in a stable, canonical order.

        Ordered alphabetically by BSSID. Stability matters because the
        index of each BSSID in this list defines the dimension index
        in every training/query vector — if the order shifts between
        bootstrap and prediction, every distance becomes meaningless.
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
        """Return (node_id, rssi_vector) pairs for every node with data.

        Each rssi_vector has length == len(list_bssid_order()), aligned
        to that order. APs not measured at a given node are filled with
        RSSI_MISSING (-100).

        Aggregation: if a (node_id, bssid) pair has multiple samples in
        the DB, the AVERAGE rssi is used. This denoises the training
        set without requiring callers to know about it.
        """
        bssid_order = self.list_bssid_order()
        bssid_index = {b: i for i, b in enumerate(bssid_order)}
        n_features = len(bssid_order)

        conn = get_connection()
        with conn.cursor() as cur:
            # AVG로 집계하여 같은 (node, bssid) 다중 샘플을 평균낸다.
            # 평균은 float 이므로 int로 캐스팅해서 반환 타입 계약을 지킴.
            cur.execute(
                "SELECT node_id, bssid, AVG(rssi) "
                "FROM fingerprint "
                "WHERE node_id IS NOT NULL AND bssid IS NOT NULL "
                "GROUP BY node_id, bssid"
            )
            rows = cur.fetchall()

        # node_id → vector(list[int]) 누적
        node_vectors: dict[str, list[int]] = {}
        for node_id, bssid, avg_rssi in rows:
            if bssid not in bssid_index:
                # bssid_order 조회 이후 누가 동시에 행을 넣은 레이스 케이스.
                # 일관성을 위해 무시한다.
                continue
            vec = node_vectors.get(node_id)
            if vec is None:
                vec = [RSSI_MISSING] * n_features
                node_vectors[node_id] = vec
            vec[bssid_index[bssid]] = int(round(float(avg_rssi)))

        return list(node_vectors.items())
