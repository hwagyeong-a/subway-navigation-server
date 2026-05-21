\# Team B 작업 종합 정리 (2026-05-20)



> 본인 (김화경) 이 5/10 \~ 5/20 까지 작업한 내용을 팀원이 한눈에 이해할 수 있도록 정리한 문서.

>  중간 미팅 자료 + 코드 리뷰 시 참고용.



\---



\## 📋 한눈에 보기



```

역할 분담:

&#x20; Team A (이예진):  Flask 백엔드 + API 라우터 + 그래프 알고리즘

&#x20; Team B (김화경):  DB 설계/구축 + KNN 위치 추정 + Wi-Fi 필터

&#x20; Team 박경찬:       데이터 수집 (RSSI + 방위각) + 앱 측 필터링

&#x20; Team 최수빈:       앱 UI



본인 작업 범위:

&#x20; subway\_server/db/        — DB 연결 + 학습 데이터 조회

&#x20; subway\_server/core/knn.py — 위치 추정 알고리즘

&#x20; subway\_server/core/wifi\_filter.py — 입력 안전망

&#x20; scripts/                 — DB 빌드/가공 SQL (v2: 5 테이블)

&#x20; docs/db-setup.md         — 팀원용 매뉴얼

```



\---



\## 🗂️ 작업한 파일 목록



\### 🆕 신규 작성 (5개)



| 파일 | 역할 |

|---|---|

| `subway\_server/core/knn.py` | KNN 위치 추정 로직 (scikit-learn) |

| `subway\_server/core/wifi\_filter.py` | 입력 Wi-Fi 안전망 필터 |

| `scripts/subway\_nav\_full.sql` | DB 스키마 + 시드 + 자동 가공 통합 (v2: 5 테이블) |

| `docs/db-setup.md` | 팀원 PC 에서 DB 재현하는 매뉴얼 |

| `worklog/2026-05-20-team-b-directions.md` | 작업 일지 |



\### ✏️ 수정 (3개)



| 파일 | 변경 내용 |

|---|---|

| `subway\_server/db/connection.py` | stub → MySQL PyMySQL 연결 구현 |

| `subway\_server/db/fingerprint.py` | stub → 새 스키마 대응 (SQL alias) |

| `subway\_server/\_\_init\_\_.py` | `init\_db(app)` 두 줄 추가 |



\---



\## 📂 파일별 상세 설명



\### 1. `subway\_server/db/connection.py` (수정)



\*\*역할:\*\* Flask 요청 단위로 MySQL connection 을 관리.



\*\*핵심 기능:\*\*



```python

def get\_connection() -> Any:

&#x20;   """현재 요청에 묶인 MySQL connection 반환.

&#x20;   같은 요청 내 재호출은 캐시된 connection 사용."""



def close\_connection(\_exc=None) -> None:

&#x20;   """요청 종료 시 connection 자동 닫기."""



def init\_db(app) -> None:

&#x20;   """create\_app() 에서 호출. teardown 훅 등록."""

```



\*\*왜 필요한가:\*\*

\- 매 요청마다 새 connection 만들면 느림 + 누수

\- 요청 단위로 캐싱 + 종료 시 자동 닫기 = 안전한 패턴

\- Flask 표준 (`flask.g` + `teardown\_appcontext`)



\*\*팀이 알아야 할 것:\*\*

\- `init\_db(app)` 가 `\_\_init\_\_.py` 의 `create\_app()` 안에서 호출되어야 함 (이미 추가됨)

\- DB 자격증명은 `app.config\["DB\_\*"]` 에서 자동으로 가져옴 (`.env` 파일 기반)



\---



\### 2. `subway\_server/db/fingerprint.py` (수정)



\*\*역할:\*\* fingerprints 테이블에서 KNN 학습 데이터 조회.



\*\*핵심 기능:\*\*



```python

class FingerprintRepository:

&#x20;   def list\_bssid\_order(self) -> list\[str]:

&#x20;       """모든 고유 BSSID(MAC) 정렬해서 반환."""

&#x20;       

&#x20;   def load\_training\_set(self) -> list\[tuple\[str, list\[float]]]:

&#x20;       """(노드ID, RSSI 벡터) 쌍을 모든 노드에 대해 반환.

&#x20;       KNN 학습 입력으로 바로 사용 가능."""

```



\*\*SQL alias 매핑 (중요!):\*\*



새 DB 스키마는 컬럼명이 바뀌었지만, KNN 코드 변경을 0줄로 만들기 위해 SQL alias 로 매핑:



```sql

SELECT 

&#x20;   location  AS node\_id,    -- 새 스키마는 'location'

&#x20;   mac       AS bssid,      -- 새 스키마는 'mac'

&#x20;   rssi\_mean AS rssi        -- 새 스키마는 'rssi\_mean'

FROM fingerprints

```



→ KNN 코드는 여전히 `bssid`, `rssi` 라는 이름으로 사용. 변경 0줄.



\*\*팀이 알아야 할 것:\*\*

\- KNN/router 측 코드는 `bssid`, `rssi` 인터페이스 그대로 유지

\- `RSSI\_MISSING = -100.0` 은 \*"이 노드에선 그 AP 신호 못 받음"\* 을 의미



\---



\### 3. `subway\_server/core/knn.py` (신규 ⭐)



\*\*역할:\*\* Wi-Fi 스캔 → 가장 가까운 노드(location) 예측.



\*\*핵심 함수:\*\*



```python

def knn\_estimate(samples: List\[WifiSample]) -> str:

&#x20;   """예: 입력 \[{bssid: '...', rssi: -48}, ...] → 출력 'b1\_stairs'"""

```



\*\*알고리즘:\*\*



\- 라이브러리: scikit-learn `KNeighborsClassifier`

\- K=3 (가까운 이웃 3개로 투표)

\- `weights='distance'` (가까운 이웃 가중치 + 동률 자동 처리)

\- `metric='euclidean'` (유클리드 거리)



\*\*CLAUDE.md 'Wi-Fi pipeline split' 준수:\*\*

```

A 의 normalize\_wifi(samples, bssid\_order)  ← 입력 정렬 (팀 A 영역)

B 의 FingerprintRepository                  ← DB 조회 (팀 B 영역)

B 의 knn\_estimate 가 위 둘을 모두 호출       ← 본인 작업

```



\*\*검증 결과:\*\*

\- 5/12 실측 데이터 4498행 학습 성공

\- `/locate` 호출 시 `{"node": "b1\_stairs"}` 정상 응답 확인 (2026-05-20)



\---



\### 4. `subway\_server/core/wifi\_filter.py` (신규)



\*\*역할:\*\* 들어온 Wi-Fi 샘플 중 신뢰할 수 없는 것 제거 (서버 측 안전망).



\*\*필터 규칙:\*\*



1\. \*\*RSSI 임계\*\* — `RSSI < -90 dBm` 약한 신호 제거

2\. \*\*이동성 SSID\*\* — `iPhone`, `Galaxy`, `\[dryer]` 등 모바일 기기 제거



\*\*박경찬님 컨셉과 일치:\*\*



```

앱 측 (박경찬):              서버 측 (본인):

&#x20; 1. RSSI ≥ -90 dBm          1. RSSI ≥ -90 dBm  (안전망 재검증)

&#x20; 2. 모바일 SSID 제외         2. 모바일 SSID 제외 (안전망 재검증)

&#x20; 3. 5초 평균

&#x20;      ↓

&#x20;  POST /locate

```



→ 앱-서버 이중 필터로 입력 안전성 확보.



\*\*현재 상태:\*\*

\- `WifiSample` dataclass 에 `ssid` 필드가 없어 SSID 필터는 자동 스킵 (`getattr` 안전 처리)

\- 추후 `ssid` 필드 추가되면 별도 코드 변경 없이 즉시 동작



\---



\### 5. `subway\_server/\_\_init\_\_.py` (수정)



\*\*변경 내용:\*\* `create\_app()` 안에 두 줄 추가.



```python

def create\_app(config\_obj: type = Config) -> Flask:

&#x20;   app = Flask(\_\_name\_\_)

&#x20;   # ... (기존 코드)

&#x20;   Swagger(app, template={...})



&#x20;   # ↓ 본인이 추가한 두 줄

&#x20;   from .db.connection import init\_db

&#x20;   init\_db(app)



&#x20;   register\_error\_handlers(app)

&#x20;   # ... (이하 기존)

```



\*\*왜 필요한가:\*\*

\- `init\_db()` 가 호출되지 않으면 MySQL connection 의 teardown 훅 등록 안 됨

\- 결과: 매 요청마다 connection 누수 → \*"Too many connections"\* 에러

\- 두 줄 추가로 누수 방지



\---



\### 6. `scripts/subway\_nav\_full.sql` (신규 ⭐) v2



\*\*역할:\*\* DB를 처음부터 끝까지 빌드하는 통합 SQL (5 테이블).



\*\*v2 주요 변경:\*\*

\- ⭐ `node\_directions` 테이블 신규 추가 (박경찬님 방위각 데이터 반영)

\- ✏️ `node\_edges` 수정: `station\_exit ↔ fare\_gate` 직접 연결 제거 → `floor1\_hall` 경유



\*\*포함 내용:\*\*



```

1\. 데이터베이스 + 5개 테이블 생성

&#x20;  - nodes (노드 마스터)

&#x20;  - node\_edges (인접 관계, 그래프 구조)

&#x20;  - node\_directions (방향 정보, 나침반 비교용) ⭐ 신규

&#x20;  - raw\_measurements (원본 측정 보관)

&#x20;  - fingerprints (KNN 학습용 통계)



2\. 시드 데이터 INSERT

&#x20;  - 노드 11개

&#x20;  - 엣지 20개 (양방향)

&#x20;  - 방위각 20개 (양방향, 절대 방위각) ⭐ 신규



3\. raw → fingerprints 자동 가공 SQL ⭐

&#x20;  - (location, mac) 기준으로 통계 자동 계산

```



\*\*node\_directions 컬럼:\*\*



| 컬럼 | 의미 | 예시 |

|---|---|---|

| `from\_node` | 출발 노드 | `station\_exit` |

| `to\_node` | 도착 노드 | `floor1\_hall` |

| `heading\_degrees` | 절대 방위각 (0\~359.9) | `268.0` |

| `cardinal` | 방향 약자 | `W` (서) |

| `clock\_position` | 시계 방향 | `9` (9시) |



\*\*자동 가공의 의미 (박경찬님 컨셉 부합):\*\*



```

\[과거: 손가공]

측정 → 별도 도구로 통계 처리 → CSV → 임포트

&#x20;               ↑

&#x20;           여기가 수동



\[현재: 자동 가공]

측정 → raw\_measurements 임포트 → SQL 1회 → fingerprints 자동 생성

&#x20;                                   ↑

&#x20;                               자동화!

```



\*\*검증:\*\*

\- 실측 데이터 4491 raw 로 테스트

\- → 483 fingerprints 생성 (원본 `all\_fingerprints.csv` 와 동일)



\---



\### 7. `docs/db-setup.md` (신규) v2



\*\*역할:\*\* 다른 팀원이 본인 PC 에서 DB 를 재현할 수 있는 매뉴얼.



\*\*v2 변경:\*\*

\- 5 테이블 기준으로 갱신

\- `node\_directions` 임포트 가이드 추가

\- 앱 측 사용법 (방위각 쿼리 예시) 추가



\*\*구성:\*\*

```

1단계: 스키마 SQL 실행 (5 테이블 + 시드 데이터 한 번에)

2단계: raw\_measurements CSV 임포트

3단계: fingerprints 채우기 (시나리오 A/B)



자주 발생하는 에러 5가지 + 해결법

node\_directions 사용법 (앱 시나리오)

```



\---



\### 8. `worklog/2026-05-20-team-b-directions.md` (신규)



\*\*역할:\*\* 본인이 5/10 \~ 5/20 까지 한 작업 일지 (worklog/README.md 양식 준수).



\---



\## 🧭 node\_directions 사용법 — 앱 시나리오



박경찬님의 \*"앱이 A→B 방위각 요청 → 서버가 그 값 리턴 → 앱이 나침반과 비교"\* 컨셉:



```

\[앱 워크플로우]

1\. KNN 으로 현재 위치 추정 → 예: "station\_exit"

2\. 다음 노드 (/route 결과로) → 예: "floor1\_hall"

3\. 서버에 "station\_exit → floor1\_hall 방위각" 요청

4\. 서버 응답: heading\_degrees = 268 (W, 9시 방향)

5\. 앱이 스마트폰 나침반과 비교

&#x20;  - 폰이 268도 근처 향하면 → "이 방향 맞음" (강한 진동)

&#x20;  - 멀어지면 → 회전 안내

```



\### SQL 쿼리 예시 (API 가 내부에서 호출)



```sql

SELECT heading\_degrees, cardinal, clock\_position

FROM node\_directions

WHERE from\_node = 'station\_exit' AND to\_node = 'floor1\_hall';



\-- 결과: 268.0, 'W', 9

```



\### 양방향 데이터 의의



박경찬님이 양방향(예: A→B, B→A) 모두 측정한 이유:

\- 계단/분기점에서 양방향이 정확히 180도 차이 안 남 (현장 측정값으로 30\~45도 오차 발견)

\- 180도 추정으로 했으면 계단 안내가 부정확했을 것

\- 본인 DB 는 측정값 그대로 보존



\---



\## 🔗 전체 시스템 흐름 — 본인 작업이 어디에 들어가는지



```

\[앱 측 (박경찬)]

&#x20;  사용자가 지하철역에서 위치/방향 확인 요청

&#x20;       ↓

&#x20;  Wi-Fi 스캔 (RSSI + BSSID)

&#x20;       ↓

&#x20;  앱 측 1차 필터: RSSI ≥ -90, 모바일 SSID 제외

&#x20;       ↓

&#x20;  5초마다 3개 평균

&#x20;       ↓

&#x20;  POST /locate { wifi: \[...] }

&#x20;               ↓

\[서버 측 (Team A 라우터)]

&#x20;  api/locate.py — 입력 검증

&#x20;       ↓

&#x20;  core/locator.py — registered estimator 호출

&#x20;               ↓

\[서버 측 (Team B 본인 ⭐)]

&#x20;  core/knn.py::knn\_estimate(samples)

&#x20;     ↓

&#x20;     core/wifi\_filter.py::filter\_wifi\_samples()  ← 서버 측 2차 필터

&#x20;     ↓

&#x20;     \_ensure\_loaded()  ← 첫 호출 시 DB 학습 데이터 로드

&#x20;               ↓

\[DB 측 (Team B 본인 ⭐)]

&#x20;  db/connection.py — MySQL connection 가져옴

&#x20;       ↓

&#x20;  db/fingerprint.py — fingerprints 테이블 조회

&#x20;               ↓

\[KNN 학습/예측 (sklearn)]

&#x20;  KNeighborsClassifier.fit() — 학습 (첫 호출 시 1회)

&#x20;  KNeighborsClassifier.predict() — 예측 (매 호출)

&#x20;               ↓

&#x20;  "b1\_stairs" 같은 노드 ID 반환

&#x20;               ↓

\[서버 응답]

&#x20;  {"node": "b1\_stairs"}

&#x20;               ↓

\[앱]

&#x20;  위치 표시 + 다음 단계로 (/route, /direction)

&#x20;               ↓

\[방향 안내 (방위각)]

&#x20;  앱이 /direction 호출 (또는 /locate 응답에 포함)

&#x20;       ↓

&#x20;  서버: node\_directions 테이블 조회 ⭐

&#x20;       ↓

&#x20;  heading\_degrees 반환 (예: 268)

&#x20;       ↓

&#x20;  앱이 폰 나침반과 비교 → 진동/음성 안내

```



→ 본인이 만든 영역이 \*\*위치 추정 + 방향 데이터 저장의 핵심\*\*.



\---



\## 🚦 팀원이 본인에게 요청할 만한 것



\### 팀 A (이예진)



| 요청 | 응답 |

|---|---|

| "DB 스키마 어디 있어요?" | `scripts/subway\_nav\_full.sql` |

| "KNN 어떻게 호출해요?" | `from subway\_server.core.knn import knn\_estimate` (자동 등록됨) |

| "WifiSample 에 ssid 추가하면?" | 본인 `wifi\_filter.py` 가 자동으로 SSID 필터 시작 |

| "init\_db 안 부르면?" | DB connection 누수. 이미 `\_\_init\_\_.py` 에 추가됨 |

| "방위각 어떻게 가져와요?" | `SELECT heading\_degrees FROM node\_directions WHERE from\_node=? AND to\_node=?` |

| "/direction 을 DB 의 방위각 쓰게 바꾸려면?" | 함께 작업 가능. db/directions.py 같이 새 repo 만드는 식 |



\### 팀 박경찬



| 요청 | 응답 |

|---|---|

| "방위각 데이터 적재됐어?" | ✅ 20개 모두 적재됨. CSV 와 동일 |

| "앱이 보내는 데이터 형식?" | `{"wifi": \[{"bssid": "...", "rssi": -48}, ...]}` |

| "데이터 수집 후 업데이트?" | raw\_measurements INSERT → 가공 SQL 1회 실행 |



\### 새로 합류한 팀원



| 요청 | 응답 |

|---|---|

| "DB 어떻게 만들어요?" | `docs/db-setup.md` 참조 |

| "본인 변경사항 어디?" | `worklog/2026-05-20-team-b-directions.md` |



\---



\## 📊 본인 작업 메트릭



```

파일 수:        8개 (신규 5 + 수정 3)

DB 테이블:      4개 → 5개 (node\_directions 추가)

시드 데이터:    nodes 11 + edges 20 + directions 20 = 51행

학습 데이터:    raw 4491 + fingerprints 483 = 4974행

관련 커밋:      18ae692, ca467cf, b9e6a13

KNN 검증:       /locate {"node": "b1\_stairs"} 응답 확인 (2026-05-20)

방위각 검증:    양방향 일관성 OK (직선 \~7°, 계단/분기점 30\~45° 측정값 보존)

```



\---



\## 🔴 미해결 



1\. \*\*`/direction` API 가 DB node\_directions 사용하도록 변경\*\*

&#x20;  - 현재: `data/nodes.json` 좌표 기반 `atan2` 계산

&#x20;  - 변경 후: `node\_directions` 테이블의 실측 방위각 그대로 리턴

&#x20;  - 팀 A + 본인 협업 필요



2\. \*\*D-09 위험 노드 정의\*\* — 계단 4개 후보



3\. \*\*`/collect` API\*\* — 앱 → DB 자동 적재 (시연 후 작업)



4\. \*\*`data/{nodes,edges,danger}.json` 갱신\*\* — 팀 A 영역



\---



\## 🟢 시연 시나리오 



```

1\. 본인 노트북 = 서버

&#x20;  - python app.py 로 Flask 서버 띄움

&#x20;  - DB 는 본인 PC 의 MySQL 사용

&#x20;  

2\. 안드폰이 Wi-Fi 핫스팟으로 본인 노트북에 연결



3\. 앱이 POST /locate 호출

&#x20;  → 본인 KNN 이 노드 ID 응답 ⭐



4\. 앱이 POST /route 호출 (팀 A)

&#x20;  → 경로 응답



5\. 앱이 POST /direction 호출 (팀 A)

&#x20;  → 방향 응답 (현재는 placeholder 좌표 기반,

&#x20;    향후 DB node\_directions 활용 예정) ⭐



6\. 사용자에게 음성/진동으로 안내

```



→  노트북 1 대로 시연 가능.



\---



\## 💪 본인이 한 일 요약



```

✅ DB 설계 + 5 테이블 구축 (4998+20행 적재)

✅ KNN 위치 추정 (scikit-learn) — 검증 완료

✅ Wi-Fi 안전망 필터

✅ 박경찬님 방위각 데이터 통합 (양방향, 측정값 보존)

✅ raw → fingerprints 자동 가공 SQL

✅ DB connection 누수 방지 (init\_db)

✅ 매뉴얼 + worklog 작성

✅ GitHub 백업 완료

```

