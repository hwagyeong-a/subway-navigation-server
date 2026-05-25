# ONBOARDING — 이 프로젝트에 처음 들어왔거나 새 세션을 시작하는 사람을 위한 가이드

> 이 문서를 **가장 먼저** 읽어주세요. 본 프로젝트의 전체 맥락·현재 상태·이어서 무엇을 해야 할지를 한 번에 정리합니다.
>
> 마지막 갱신: **2026-05-25**
> 다음 마일스톤: **2026-06-12 최종 발표 / 2026-06-19 최종 제출**

---

## 0. 한 줄 요약

> **시각장애인용 지하철역 보행지원 시스템**의 Flask 서버 (팀원 A 영역). 데이터·KNN·앱 1차 다 끝났고 **서버 호스팅 + 통합 테스트** 단계.

---

## 1. 너는 누구이고 어떤 역할인가

이 저장소는 **이예진(팀원 A)** 의 서버 영역. Claude 세션을 새로 열었다면 메모리에서 다음 사실을 인지하고 시작:

| 항목 | 값 |
|---|---|
| 사용자 이름 | **이예진** |
| 학교 | 아주대학교 |
| 팀명 | 우당탕탕 |
| GitHub 사용자 | `lowelllll` |
| GitHub 조직 | `ajou-udangtangtang` |
| 본인 역할 | **팀원 A** — Flask 백엔드 + API + 경로/방향 로직 |
| 본인 영역 코드 | `subway_server/api/`, `subway_server/core/graph.py` `direction*` `route*` |
| **건드리면 안 되는 영역** | `subway_server/db/`, `subway_server/core/knn.py`, `subway_server/core/wifi_filter.py`, `scripts/` (모두 화경 영역) |

### 팀원

| 팀원 | 영역 | 비고 |
|---|---|---|
| **박경찬** | 조장, 데이터 수집, 안드로이드 앱 측 보조 도구 | 절대방위각 데이터·DB 스키마 작성 |
| **김화경** | 팀원 B — MySQL DB + KNN + Wi-Fi 필터 | PR #1 머지 완료 (5/21) |
| **이예진(본인)** | 팀원 A — Flask 서버 + API | 본 저장소 주인 |
| **최수빈** | 안드로이드 메인 앱 | 별도 repo: `csb2000/subway-navigation-app` |

---

## 2. 프로젝트가 뭐냐 (30초 버전)

- **목적**: 지하철역 안에서 시각장애인이 자율적으로 길을 찾을 수 있게 안내
- **위치 추정**: GPS X (지하), **Wi-Fi Fingerprinting + KNN**
- **방향 안내**: 노드 그래프 + 박경찬 실측 절대 방위각 + 폰 나침반 비교 → 진동 + TTS
- **대상 역**: 1개 역 (11 노드: 출입구·홀·개찰구·계단·승강장 등)

### 시스템 구성

```
[안드로이드 앱 (최수빈)]
   │ HTTP POST (JSON)
   ▼
[Flask 서버 (본인)] ─── [MySQL (화경)]
   │  POST /locate     → KNN → 노드 ID
   │  POST /route      → Dijkstra → path with edge_type
   │  POST /direction  → JSON 조회 → angle/cardinal/clock
```

상세 시스템 다이어그램은 `docs/03-시스템아키텍처.md`.

---

## 3. 지금 (2026-05-25) 어디까지 됐나

### ✅ 완료 — 개별 부품 100%

| 영역 | 담당 | 결과물 |
|---|---|---|
| 데이터 수집·정제 (11 노드·20 방위각·4998 fingerprint 행) | 박경찬 | `data/*.json` + DB 시드 |
| MySQL DB 구축 + KNN + Wi-Fi 필터 | 김화경 | `scripts/subway_nav_full.sql`, `subway_server/core/knn.py`, `wifi_filter.py` |
| Flask 서버 + 3 API + Swagger UI | 본인 | `subway_server/`, `app.py` |
| 단위 + 통합 + E2E (HTTP smoke + Playwright UI) 테스트 72개 | 본인 | `tests/` |
| 안드로이드 앱 1차 (4 화면 + TTS + 진동) | 최수빈 | `csb2000/subway-navigation-app` |

### 🟡 현재 임계 경로 — **서버 호스팅**

최수빈 앱이 `/locate /route /direction` 을 호출할 수 있어야 통합 테스트 가능. 호스팅 옵션 미결.

### ⏳ 6/12 발표까지 남은 작업

1. 서버 호스팅 결정 + 실행 (ngrok / 학내 / 클라우드 무료)
2. 앱 ↔ 서버 통합 테스트
3. 실제 지하철역 현장 테스트 (KNN 위치 추정 정확도 검증)
4. 시연 시나리오 합의 (출발지·목적지)
5. 최종 발표 자료 + 영상

---

## 4. 어떻게 이어서 작업하나

### 4.1 환경 셋업 (새 머신에서)

```bash
git clone https://github.com/ajou-udangtangtang/subway-navigation-server.git
cd subway-navigation-server

python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env               # DB 자격증명 등 수정 필요시
```

### 4.2 테스트 (MySQL 없이도 가능)

```bash
pytest tests/unit tests/integration -q   # 빠른 로컬, 59 tests
playwright install chromium               # E2E 첫 1회만 (~150MB)
pytest tests/e2e -v                       # 실 서버 띄우고 13 tests
pytest                                    # 전체 72 tests
```

기대: `72 passed in ~4초`

### 4.3 서버 띄우기

```bash
python app.py
# http://127.0.0.1:5000
```

스모크:
```bash
curl -X POST http://127.0.0.1:5000/direction \
  -H "Content-Type: application/json" \
  -d '{"from":"station_exit","to":"floor1_hall"}'
# → {"angle":268,"cardinal":"W","clock":9}
```

Swagger UI: http://127.0.0.1:5000/apidocs

---

## 5. 가장 먼저 읽어야 할 문서 (우선순위 순)

1. **본 ONBOARDING.md** — 너는 지금 여기 있음
2. `CLAUDE.md` — 코드 컨벤션·통합 경계·금지 사항
3. `docs/10-진행이력.md` — 프로젝트 전체 흐름 + 의사결정 이력
4. `docs/05-API명세.md` — 3 API 의 입출력 contract
5. `docs/12-2차개발계획.md` — 최근 실행한 큰 작업의 계획서
6. `worklog/2026-05-25-team-progress-update.md` — 최근 동기화 일지
7. `docs/11-수집데이터구조.md` — 박경찬 데이터 5종 구조
8. `docs/06-데이터모델.md` — DB·JSON 스키마
9. `docs/09-위험요소및결정항목.md` — 결정 항목 (D-01, D-02 등 ✅ 완료)

코드 작업 전:
- `subway_server/__init__.py` — 앱 팩토리·통합 경계
- `subway_server/core/graph.py` — 그래프 모델·Dijkstra
- `subway_server/api/` — 3 endpoint
- `tests/conftest.py` + `tests/e2e/conftest.py` — 픽스처

---

## 6. 핵심 설계 결정 (왜 이렇게 됐는지)

### 6.1 좌표(x, y) 없음 — 방위각만 사용
박경찬 실측 데이터에 (x, y) 가 없음. `node_directions` 에 `(from, to)` 별 `heading_degrees` 만 저장.
`/direction` API 는 DB/JSON 조회로 응답 (이전엔 `atan2` 계산).

### 6.2 위험 노드 회피 로직 제거
docs 초기엔 `danger.json` 으로 노드를 회피했으나, 실 데이터는 `edge_type` (`flat`/`stairs`/`branch`) 으로 표현. 회피 대신 *"계단을 내려가세요"* 같은 안내 카테고리로 활용.

### 6.3 노드 ID 의미 ID 채택
`A`, `B`, `C` 같은 알파벳 → `station_exit`, `fare_gate` 등 의미 ID. 디버깅·시연 시 가독성 ↑.

### 6.4 좌표계: 정북=0°, 시계방향 양수
폰 나침반과 직접 비교 가능. 박경찬 실측이 이 규약 사용.

### 6.5 Team B 통합 경계
`subway_server/core/locator.py` 의 `register_estimator()` 패턴.
- 화경의 `knn.py` 가 startup 시 자동 등록
- 본인 코드는 `estimate(samples) -> str` 만 호출
- 테스트에선 `fake_estimator` fixture 로 격리

### 6.6 docs §9.3.1 D-01, D-02 ✅ 해소
좌표계·노드 ID 둘 다 결정 완료. docs/09 참조.

---

## 7. 본인이 자주 잊는 / 헷갈리는 것

- **본인 이름**: 이예진 (NOT 박경찬 — 이메일 핸들이 `qkrrudcks999`라 종종 혼동)
- **중간 미팅**: 5/15 → 5/22 로 변경되었고 5/22 진행 완료됨
- **최수빈 안드로이드 repo**: 우리 org 가 아니라 `csb2000/subway-navigation-app` (개인 repo)
- **화경 fingerprints 컬럼**: 우리가 `bssid/rssi` 라 부르지만 DB 실 컬럼은 `mac/rssi_mean`. SQL alias 로 매핑됨 (`db/fingerprint.py`)
- **edges 양방향**: `data/node_edges.json` 은 `A→B`, `B→A` 모두 명시 (대칭 검증됨)
- **directions 20개 vs edges 21개**: `b1_down_stairs_front ↔ b1_up_stairs_front` 쌍 중 한 방향만 directions 에 있을 가능성. 부분 매치로 검증 중

---

## 8. 새 세션에서 자주 묻는 질문

### Q. 테스트 어떻게 돌리지?
```bash
pytest -q
```

### Q. 서버 뭐 어떻게 띄우지?
```bash
python app.py
```
또는 host/port override:
```bash
FLASK_HOST=0.0.0.0 FLASK_PORT=8080 python app.py
```

### Q. Swagger UI 어디?
http://127.0.0.1:5000/apidocs

### Q. 화경 코드 봐도 됨?
보기 OK, **수정 X**. 머지 충돌 방지. `docs/team-b-work-summary.md` 가 정리해둠.

### Q. 본인 영역인데 갈아엎고 싶음
가능. 단, `tests/unit/test_direction.py` 의 좌표계 컨벤션 (정북=0, CW) 은 contract — 바꾸려면 팀 합의 필요.

### Q. 안드로이드 앱 동작 어떻게 확인?
별도 repo (`csb2000/subway-navigation-app`) clone. 단톡방 5/24 22:45 메시지 참조.

### Q. 다음에 뭐 하면 됨?
§3의 *"⏳ 6/12 발표까지 남은 작업"* 참조. 1번 (서버 호스팅) 부터.

---

## 9. 단톡방·외부 자원

- 단톡방: 카카오톡 "우당탕탕 졸업프로젝트"
- 팀즈 채널: 박경찬 5/3 공유 링크 (프로젝트 명세·수집 데이터)
- 서버 repo: https://github.com/ajou-udangtangtang/subway-navigation-server
- 앱 repo: https://github.com/csb2000/subway-navigation-app
- 화경 fork: https://github.com/hwagyeong-a/subway-navigation-server (백업용)
- Claude MAX 학교 지원 계정: 박경찬 관리 (학교 메일 등록됨)

---

## 10. Claude 메모리 컨벤션

이 저장소에서 작업하는 Claude 세션은 다음 규칙을 따른다.

1. **본인 정보는 Claude 의 auto-memory (`~/.claude/projects/-Users-lowell/memory/`) 에 저장됨** — 이예진, 우당탕탕 팀, 졸업프로젝트 등
2. **작업 후 반드시 `worklog/YYYY-MM-DD-<slug>.md` 작성** — 일자별 1개. 템플릿은 `worklog/README.md`
3. **새 코드 작성 전 관련 docs 먼저 확인** — §5 우선순위 따라
4. **테스트 깨면 안 됨** — `pytest -q` 그린 유지
5. **화경 영역 파일 수정 X**
6. **`docs/05-API명세.md` 변경 시 Swagger spec (endpoint docstring) 동기화**

---

## 11. 빠른 점검 체크리스트 (새 세션에서)

- [ ] `git status` 깨끗한가? → 깨끗하지 않다면 commit 또는 stash
- [ ] `git pull origin main` 했는가?
- [ ] `pytest -q` 72 그린인가?
- [ ] 최근 worklog 읽었는가? (`worklog/` 마지막 파일)
- [ ] `docs/10-진행이력.md` 마지막 Phase 읽었는가?

위 5개가 ✅ 라면 작업 시작 OK.
