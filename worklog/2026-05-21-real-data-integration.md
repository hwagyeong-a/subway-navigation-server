# 2026-05-21 — 실데이터 통합 + E2E 테스트 + Playwright Swagger UI 검증

## 한 일
- `data/` 폴더를 fictional A-F 그래프 → 박경찬 실측 11 노드 데이터로 교체
  - `nodes.json` 재작성 (좌표 제거, `floor`/`zone`/`description` 추가)
  - `node_edges.json` 신설 (객체 배열 + `edge_type`)
  - `node_directions.json` 신설 (절대 방위각 20개)
  - `edges.json`, `danger.json` 폐기
- `subway_server/core/graph.py` 재작성 — `NodeMeta`/`Edge`/`Direction` dataclass + hop-count Dijkstra
- `subway_server/core/direction.py` 삭제 (atan2 헬퍼 불필요)
- `subway_server/api/errors.py` 에서 `DangerDestinationError` 제거
- `subway_server/api/direction.py` 재작성 — DB 조회 기반, `angle`/`cardinal`/`clock` 3필드 응답
- `subway_server/api/route.py` 갱신 — 응답에 `floor`/`zone`/`edge_to_next` 메타 포함
- 단위 테스트 33개 (test_graph 18 + test_direction 7 + test_wifi 6) — 전부 그린
- 통합 테스트 26개 (direction 7 + route 11 + locate 7 + health 1) — 전부 그린
- **E2E 테스트 신설 (`tests/e2e/`)**:
  - `conftest.py` — `live_server` fixture (Flask subprocess + 헬스체크 폴링)
  - `test_http_smoke.py` 9개 — `requests` 라이브러리로 실서버 호출 검증
  - `test_swagger_ui.py` 4개 — **Playwright Chromium**으로 Swagger UI 인터랙션 + 발표 자료용 스크린샷 2장
- `playwright install chromium` 설치 (~92MB 1회만)
- docs 갱신: `05-API명세.md` (direction/route 응답 형식), `09-위험요소및결정항목.md` (D-01, D-02 ✅), `CLAUDE.md` (좌표계 섹션 갱신), `README.md` (curl 예제, E2E 안내)
- `docs/12-2차개발계획.md` 작성·푸시 (커밋 `da829bd`)
- `requirements.txt` 갱신: `pytest-playwright`, `playwright`, `requests` 추가

## 왜 이렇게 했는지
- 박경찬님 New_DB(5/20) 자료가 모두 들어왔고 화경님 PR 머지(5/21)도 끝나, 본인 영역만 fictional 데이터를 사용 중이었음 — 일관성 회복
- 좌표(x, y) 가 박경찬 자료에 없고 `node_directions` 가 실측값으로 제공되어, atan2 계산 자체가 무의미해짐. JSON/DB 조회로 단순화
- E2E HTTP smoke 는 Flask test client 가 잡지 못하는 *진짜* 통신 문제 (포트 바인딩, JSON 직렬화 회귀 등) 를 검증할 수 있어 가치 큼
- Playwright 는 *"Swagger UI 가 실제로 잘 뜨는지"* 라는 회의적 질문에 대한 자동화된 답. 발표 자료용 스크린샷도 동시에 산출
- 화경 코드 영역(`db/`, `core/knn.py`, `wifi_filter.py`) 절대 안 건드림 — 머지 충돌 0

## 막힌 것 / 결정 미뤄진 것
- 초기 Playwright 테스트에서 `<.opblock-summary-path>` 의 path 텍스트 앞에 `​` (zero-width space) 가 붙어 정확 일치 실패 → 부분 매치(`in`) 로 수정. Swagger UI 의 내부 렌더링 특성, 이후 동일 패턴 사용 권장
- `/locate` 의 **실 KNN 동작 E2E** 는 MySQL 의존이라 본 작업에서 제외. 화경 영역과의 통합 E2E 는 별도 세션에서 작업 예정
- 시연 노드 ID 가 의미 ID(`station_exit`)로 결정되어 docs §9.3.1 D-02 자동 해소 — 추가 작업 없음

## 다음에 할 일
- 5/22 21:00 중간 미팅에서 *"여기까지 끝남, 다음은 앱 통합"* 으로 발표
- 안드로이드 측(최수빈)과 통신 형식 최종 확인 — 새 `/direction` 응답(3필드)·새 `/route` 응답(객체 배열) 형식 공지
- (선택) `/locate` E2E with real KNN — MySQL 통합

## 관련 커밋
- `da829bd` docs: add 2차 개발 계획 (실데이터 통합 + E2E 테스트)
- `946cd07` feat: integrate 박경찬 real data + add E2E (Playwright Swagger UI) tests
