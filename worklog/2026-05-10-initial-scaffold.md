# 2026-05-10 — Initial scaffold (Flask + 3 APIs + tests + Swagger)

## 한 일

- Flask 앱 팩토리 (`subway_server/__init__.py`) + entry point (`app.py`) 작성
- 3개 API 엔드포인트 모두 구현
  - `POST /direction` — `atan2` 기반 절대 각도 계산 (북=0, CW)
  - `POST /route` — Dijkstra (`heapq`) + 위험 노드 자동 제외
  - `POST /locate` — 입력 검증 + 등록된 estimator 호출 (KNN 미연동 시 `KNN_ERROR` 500)
- Team B 통합 경계 (`core/locator.py`): `LocationEstimator` callable + `register_estimator()` 패턴
- 데이터: `data/{nodes,edges,danger}.json` (6노드 샘플 그래프)
- 테스트 인프라: `pytest` + 앱 팩토리 fixture + `fake_estimator` fixture
- 단위 테스트 29개 + 통합 테스트 19개 = **48 tests, all green**
- Swagger UI 통합 (`flasgger`) — 엔드포인트 docstring으로 OpenAPI spec 작성, `/apidocs` 자동 생성
- 에러 envelope 표준화 (`api/errors.py`) — `docs/05-API명세.md §5.5` 와 일치
- DB 영역은 stub만 (`db/fingerprint.py`, `db/connection.py`) — Team B가 채울 자리
- `CLAUDE.md` 작성 (향후 Claude 세션 가이드)
- `worklog/` 폴더 + 작성 규칙 문서화

## 왜 이렇게 했는지

- **`subway_server/` 패키지 구조 채택**: pytest의 import path 문제 회피 + 절대 임포트 일관성. `docs/§7.2.3` MVP 단일파일 구조는 "테스트 필수 + 확장성" 두 요건을 동시에 만족하지 못해 거부.
- **Team B 경계로 Protocol/ABC 대신 module-level callable 채택**: 한 명짜리 구현에 클래스 계층은 과함. Python data/ML 코드는 함수 패턴이 더 자연스러움.
- **`flasgger` 채택** (vs `flask-smorest`, `Flask-RESTX`): 데코레이터/YAML docstring 한 가지만 알면 됨. 학습 부담 최소.
- **좌표계 변환을 4개 cardinal direction unit test로 못 박음**: `atan2` native(동=0, CCW)와 우리 규약(북=0, CW) 사이의 변환은 가장 자주 나는 버그 지점.
- **앱 팩토리에서 `core/knn` 자동 로드 시도 + 실패 시 stub 유지**: Team B가 `knn.py` 추가하면 코드 변경 없이 자동 연결.

## 막힌 것 / 결정 미뤄진 것

- Team B와 합의 필요한 항목 (`docs/09 §9.3`):
  - D-02: 노드 ID 컨벤션 (현재 데모는 `A`~`F`. 운영용은 의미 ID 권장 — 미합의)
  - D-05: KNN K 값 (현재 `.env.example`에 5 권장)
  - D-09: 위험 노드 항목 정의 (현재 데모는 `E` 하나만)
- Team C/D(앱)와 합의 필요:
  - 통신 URL/포트 (현재 5000)
  - CORS 정책 — 미설정. 앱이 다른 호스트에서 호출 시 추가 필요할 수도
- macOS 자동 모드가 dev server 바인딩(`0.0.0.0:5000`)을 차단 — `app.py`는 그대로 두고 스모크는 Flask test client로 수행. 본인이 직접 `python app.py` 돌릴 때는 문제 없음.

## 다음에 할 일

- 5/15 중간 미팅 자료 준비 (`docs/03-시스템아키텍처.md` + `docs/05-API명세.md` 기반 슬라이드 + 라이브 데모)
- Team B에게 인터페이스 contract 전달:
  - `LocationEstimator` 시그니처
  - `WifiSample` dataclass
  - `FingerprintRepository` 스텁 메소드 시그니처
  - `core/wifi.py::normalize_wifi` 활용법
- 안드로이드 팀과 통신 합의 (URL/CORS/JSON 형식 최종 확인)

## 관련 커밋

- `bb17d51` feat: initial Flask scaffold with 3 APIs, tests, and Swagger UI
- `0a354d3` docs(worklog): record commit hash for initial scaffold entry

## 후속 수정

- Swagger UI에서 request body 예시가 안 보이는 이슈 수정. 원인: flasgger 기본 spec이 Swagger 2.0인데 docstring이 OpenAPI 3.0 문법(`requestBody`/`content`)으로 작성됨. Swagger 2.0의 `parameters` + `in: body` 형식으로 3개 endpoint(`/locate`, `/route`, `/direction`) docstring 변환. 응답 예시도 함께 보강.
- `app.py` 의 host 기본값을 `0.0.0.0` → `127.0.0.1` 로 변경 (로컬 개발용으로 더 안전). `FLASK_HOST` env로 override 가능.
