# 2026-05-13 — Team B 구현 (DB connection + fingerprint repo + KNN locator)
## 한 일
- MySQL 스키마 세팅 (`scripts/schema.sql`)
  - `subway_nav` 데이터베이스 + `fingerprint` 테이블 생성
  - 컬럼 제약: `node_id NOT NULL`, `bssid VARCHAR(17) NOT NULL`, `rssi INT NOT NULL`
  - 조회 성능용 인덱스 2개 (`idx_fp_node`, `idx_fp_bssid`)
  - 시연용 시드 데이터 9행 (A/B/C 노드 × AP 3개)
- DB 연결 모듈 구현 (`subway_server/db/connection.py`) — Team A stub 교체
  - `flask.g` 기반 요청 스코프 connection 캐싱
  - `teardown_appcontext` 훅으로 요청 종료 시 자동 close
  - `init_db(app)` 헬퍼 추가 — `create_app()`에서 호출 필요
- Fingerprint 저장소 구현 (`subway_server/db/fingerprint.py`) — Team A stub 교체
  - `list_bssid_order()` — BSSID 알파벳 오름차순 고정
  - `load_training_set()` — 노드별 RSSI 벡터 생성, 미측정 AP는 `-100`으로 패딩
  - 같은 (node, bssid) 다중 샘플은 SQL `AVG()`로 평균 집계
  - `RSSI_MISSING = -100` 상수 정의 (KNN 입력 처리와 공유)
- KNN 위치 추정기 구현 (`subway_server/core/knn.py`)
  - `knn_estimate(samples) -> str` — Team A의 `_try_register_real_estimator()`가 자동 등록
  - K=3 다수결, 동률 시 거리 합 최소 규칙
  - 학습 데이터는 첫 호출 시 모듈 전역에 캐시 (`_loaded` 플래그)
  - 유클리드 거리, 빈 샘플은 `ValueError`, 학습 데이터 없으면 `RuntimeError`
## 왜 이렇게 했는지
- **K=1 아닌 K=3 채택**: 노드당 다중 샘플(현장 측정 노이즈) 가정. 1-NN은 튀는 샘플 하나에 끌려가 시연 중 점프할 위험 큼. 동률 시 거리 합 최소 규칙으로 결정성 확보.
- **학습 데이터 모듈 캐시 (DB 1회 로드)**: 매 `/locate` 호출마다 fingerprint 전체를 다시 읽는 건 낭비. 데이터 갱신은 *오프라인 수집 → DB 재적재 → 서버 재시작* 흐름이라 런타임 reload 불필요.
- **`__init__`에서 DB 안 만짐**: 초기 버전은 `KNNLocator.__init__`에서 `get_connection()`을 호출했는데, Flask 앱 컨텍스트 밖에서 import될 때 `RuntimeError: Working outside of application context`로 죽음. 모듈 전역 lazy load 방식으로 변경.
- **`FingerprintRepository`에 인자 없음**: connection을 생성자로 받지 않고 각 메서드에서 `get_connection()` 호출. 요청 스코프 connection과 자연스럽게 맞물림.
- **BSSID 정렬 = 알파벳 오름차순**: README "구현 우선순위" 표의 단순화 기조와 일치. 정렬 정교화는 후순위.
- **AVG 집계를 SQL에 위임**: Python에서 그룹핑하면 fingerprint 전체를 메모리로 끌어와야 함. SQL이 더 효율적. 평균은 float 반환이므로 `int(round(float(...)))`로 타입 계약 유지.
- **BSSID 컬럼을 `VARCHAR(17)`로 축소** (초기 `VARCHAR(100)` 대비): MAC 주소는 `aa:bb:cc:dd:ee:ff` 17자 고정. 인덱스 효율과 의도 명시성 모두 개선.
## 막힌 것 / 결정 미뤄진 것
- Team A에게 요청 필요한 항목:
  - `subway_server/__init__.py`의 `create_app()` 안에 두 줄 추가:
```python
    from .db.connection import init_db
    init_db(app)
```
    안 넣으면 매 요청마다 connection이 누수되어 MySQL `max_connections` 도달 시 서버 사망
  - `subway_server/core/locator.py`에 `WifiSample` dataclass 정의 확인 (knn.py가 import). 필드명은 `bssid`, `rssi`로 가정 — 다르면 알려주기
  - `/locate` 라우터가 `knn_estimate`의 `ValueError`/`RuntimeError`를 잡아 `KNN_ERROR` (500)으로 응답하는지 확인
- Team B 내부 미해결 (`docs/09 §9.3`):
  - D-04: 노드당 fingerprint 샘플 수 — 현재 1샘플/노드. 실제 데이터 수집 시 다중 샘플 정책 합의 필요
  - D-05: KNN K 값 — 코드는 K=3 하드코딩. 추후 데이터 양에 따라 조정 가능성
- 인덱스 누락 시행착오: `CREATE INDEX idx_fp_node` 한 줄을 실수로 건너뛰어 `SHOW INDEX` 출력에 2개만 나옴. 재실행으로 해결. 스키마 스크립트는 모든 인덱스 포함으로 정리 완료.
## 다음에 할 일
- `tests/integration/test_mysql.py` 작성 — DB 연결, BSSID 정렬, training set 로드 검증
- Team A의 `__init__.py` 패치 머지 후 `/locate` end-to-end 테스트
  - 예상 입력: 노드 A 패턴(`-45, -75, -80`) → `{"node": "A"}` 반환
- 5/15 중간 미팅 전 시연 시나리오 검증 (노트북 + MySQL Workbench + Postman)
- 실제 지하철역 Wi-Fi 데이터 수집 일정 Team A와 조율
- 데이터 수집 후 K=3 vs K=5 시연 환경 비교 검증
## 관련 커밋
- `feat(db): MySQL PyMySQL 연결 구현`
- `feat(db): fingerprint 저장소 구현`
- `feat(core): KNN 위치 추정 모듈 구현`
- `chore(db): fingerprint 테이블 스키마 및 시드 데이터 추가`
## 후속 수정
- `FingerprintRepository(conn)` 호출 제거. 초기 버전이 생성자에 connection을 넘기는 형태였는데 새 저장소 인터페이스는 인자를 받지 않음. `repo = FingerprintRepository()` 로 변경.
- `init_knn()` 함수 폐기. Team A의 `_try_register_real_estimator()`가 `from .core.knn import knn_estimate`를 자동 import하는 패턴이라 별도 초기화 함수 호출 불필요. `app.py`에서 `init_knn()` 호출하던 부분도 제거.
- `best_node == "UNKNOWN"` 문자열 반환 제거. 빈 결과를 문자열로 반환하면 그래프 탐색 단계에서 *"UNKNOWN 노드 없음"* 에러로 디버깅 어려움. `RuntimeError`로 명시적으로 던지고 Team A의 에러 핸들러가 `KNN_ERROR` (500)으로 잡는 흐름으로 통일.
