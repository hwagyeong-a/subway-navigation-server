# 2026-05-25 — 서버 호스팅(ngrok) + 로컬 DB 구축 + 실데이터 검증

## 한 일
- **로컬 Docker MySQL 구축** (`subway_nav`, 포트 6306)
  - `scripts/subway_nav_full.sql` 적재 → 11 노드 / 20 엣지 / 20 방위각
  - `all_filtered_raw.csv` → `raw_measurements` 4491행 (Python `pymysql` 로더)
  - 집계 SQL 재실행 → `fingerprints` 483행 (151 MAC × 11 노드)
  - `.env` 생성 (DB_HOST=127.0.0.1, DB_PORT=6306, DB_NAME=subway_nav) — gitignore 됨
- **scikit-learn 누락 수정** — 화경 `core/knn.py` 가 import 하나 `requirements.txt` 에 없어 `/locate` 가 stub fallback(`KNN_ERROR`) 중이었음. 추가 후 `/locate` 실동작 (커밋 `25f1df7`)
- **ngrok 으로 서버 외부 공개**
  - 고정 dev 도메인 `https://sporty-press-unfeeling.ngrok-free.dev` (계정 귀속, 재시작해도 동일)
  - Flask 포트 5001 (5000 은 macOS AirPlay/ControlCenter 충돌)
- **Swagger requestInterceptor** — Try-it-out 요청에 `ngrok-skip-browser-warning` 헤더 자동 주입 (커밋 `fe51501`)
- **실데이터 검증 스크립트** `scripts/verify_api_with_real_data.py` (커밋 `b13104e`)
  - `/locate` 110/110 정확도 100%
  - `/route` 110/110 노드 쌍 도달
  - `/direction` 20/20 엣지 응답

## 왜 이렇게 했는지
- **ngrok 채택**: 최수빈 앱 통합 테스트를 위한 실서버 주소가 필요했음. GCP 는 2~3시간 셋업이고 발표용으로는 추후에, 지금은 5분이면 되는 ngrok 으로 빠르게 연결. 무료 dev 도메인이 고정이라 주소 재공유 부담도 없음.
- **로컬 Docker MySQL**: 화경 DB 가 화경 머신에만 있어, 본인 머신에서 `/locate` 를 돌리려면 동일 DB 가 필요. 화경 `subway_nav_full.sql` + 박경찬 raw CSV 로 재현.
- **검증 스크립트를 committed tool 로**: 데이터/코드 바뀔 때마다 재실행해 회귀 확인 가능. 발표 자료용 수치도 산출.

## 막힌 것 / 결정 미뤄진 것
- **/locate 100% 는 data leakage** — fingerprints(평균)가 검증에 쓴 raw 와 같은 데이터에서 나옴. 진짜 정확도는 현장 신규 측정으로 held-out 테스트 필요 (현장 테스트 단계).
- **ngrok 은 노트북 의존** — 본인 노트북 + Flask + ngrok 실행 중일 때만 동작. 발표용 상시 호스팅(GCP)은 추후 결정.
- **/route 응답 형식 변경 주의** — 단순 문자열 배열이 아니라 객체 배열(node/floor/zone/edge_to_next). 최수빈 앱이 옛 형식 가정 시 파싱 수정 필요 — 통합 테스트에서 확인할 것.

## 다음에 할 일
- 최수빈과 시간 조율 → 앱이 ngrok 주소로 4개 화면 통합 테스트
- 통합 중 `/route` 응답 형식 등 호환성 이슈 확인
- (발표 임박 시) GCP 영구 호스팅 검토

## 관련 커밋
- `25f1df7` fix(deps): add scikit-learn to requirements.txt
- `fe51501` feat(swagger): auto-inject ngrok-skip-browser-warning header
- `b13104e` test: add real-data API verification script
- `164871f` docs: record 2026-05-25 hosting + verification progress

## 로컬 실행 메모 (재현용)
```bash
# 1. Docker MySQL 떠있는지 확인 (포트 6306, root/lowell, subway_nav)
# 2. Flask 서버
cd ~/dev/src/subway-navigation-server && source .venv/bin/activate
FLASK_PORT=5001 python app.py
# 3. ngrok (고정 도메인)
ngrok http --url=sporty-press-unfeeling.ngrok-free.dev 5001
# 4. 검증
python scripts/verify_api_with_real_data.py
```
