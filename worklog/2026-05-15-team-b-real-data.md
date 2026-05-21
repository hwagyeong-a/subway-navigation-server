# 2026-05-15 — 실측 데이터 도입 (새 스키마 + sklearn KNN + Wi-Fi 필터)

## 한 일
- DB 스키마 전면 교체 (`subway_nav.sql`) — 4 테이블 (`nodes`, `node_edges`, `raw_measurements`, `fingerprints`)
- 실측 데이터 임포트 — nodes 11개, node_edges 20개, raw_measurements 4491행, fingerprints 483행
- `db/fingerprint.py` 새 스키마 대응 — SQL alias 매핑 (`mac AS bssid`, `rssi_mean AS rssi`)로 KNN 인터페이스 유지
- `core/knn.py` 신규 작성 — scikit-learn `KNeighborsClassifier(K=3, weights='distance')` 채택
- `core/wifi_filter.py` 신규 작성 — RSSI < -90 dBm 안전망 필터
- `docs/db-setup.md` 작성 — 팀원 PC에서 DB 재현하는 매뉴얼

## 왜 이렇게 했는지
- **SQL alias로 컬럼명 매핑**: 새 스키마는 `mac`, `rssi_mean`이지만 KNN 코드는 기존 `bssid`, `rssi` 의미를 유지. alias가 매핑 비용을 repository 한 곳에 가둬 KNN/router 코드 변경 0줄
- **scikit-learn 채택**: `weights='distance'`가 동률 처리를 자동으로 해줌. 11노드 × 151차원이라 학습 속도/메모리 부담 무시 가능. 직접 구현했던 동률 처리 로직 폐기
- **AVG() 제거**: 새 스키마는 이미 `rssi_mean` 으로 통계가 계산되어 있어 SQL 집계 불필요. KNN 직접 호출 1회로 단순화
- **WifiSample의 ssid 필드 없음 확인**: `api/locate.py` 검증이 `bssid`, `rssi`만 받음. wifi_filter는 SSID 기반 모바일 기기 필터 제거, RSSI 임계만 적용

## 막힌 것 / 결정 미뤄진 것
- **Import Wizard 인코딩 에러** (`'cp949' codec can't decode...`): description 한글 때문. nodes/node_edges는 SQL 직접 INSERT로 우회. raw/fingerprints는 한글 없어서 Wizard 진행
- **fingerprints Import 에러** (`Column 'ssid' specified twice`): CSV의 `node_order` 컬럼이 fingerprints 테이블에 없어 매핑 충돌. Configure 화면에서 `node_order` 체크 해제로 해결
- **`subway_server/__init__.py`에 `init_db(app)` 두 줄 추가 필요** — Team A 확인 대기. 안 넣으면 매 요청마다 MySQL connection 누수
- **`data/{nodes,edges,danger}.json` 새 노드 ID로 갱신 필요** — 기존 A~F → `station_exit` 등 11개. Team A와 협의 필요
- **위험 노드 정의** (D-09): 계단(stairs zone) 4개 후보 (`floor1_stairs`, `stairs_mid`, `b1_stairs`, `b1_up_stairs_front`). 시각장애인 안전 관점에서 어디까지 회피 대상인가는 5/15 미팅 안건
- **노드 좌표**: placeholder 상태. 실측 좌표는 5/22 측정 예정

## 다음에 할 일
- 로컬에서 `python app.py` + `/apidocs` 에서 `/locate` end-to-end 검증
- Team A에게 `init_db(app)` 패치 및 `data/*.json` 갱신 요청 전달
- `docs/06-데이터모델.md` 6.6 변경 이력 섹션 추가 (시연 후)

## 관련 커밋
- `chore(db): 새 스키마(4 tables) MySQL 변환 및 시드 데이터 추가`
- `refactor(db): fingerprint repo 새 스키마 대응 (SQL alias 매핑)`
- `feat(core): scikit-learn KNeighborsClassifier 채택`
- `feat(core): Wi-Fi 안전망 필터 (RSSI≥-90)`
- `docs: DB 구축 매뉴얼 추가 (팀원 PC 재현용)`
