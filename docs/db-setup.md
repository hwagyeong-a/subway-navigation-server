\# subway\_nav DB 구축 매뉴얼 (v2)



> 다른 PC에서 같은 DB를 재현하려면 이 매뉴얼을 따라 하세요.

> 처음 시도 시 약 30분\~1시간, 익숙해지면 15분 정도 소요됩니다.

> 막히는 부분은 아래 "자주 발생하는 에러" 섹션 참고.

>

> \*\*v2 변경 사항 (2026-05-20):\*\*

> - `node\_directions` 테이블 추가 (방향 정보 전담)

> - `node\_edges` 의 station\_exit/fare\_gate 직접 연결 → floor1\_hall 경유로 수정



\## 📦 준비물



\- \*\*MySQL 8.0 이상\*\* 설치

\- \*\*MySQL Workbench\*\* (관리 도구)

\- 팀에서 받은 \*\*CSV 파일 2개\*\*:

&#x20; - `all\_filtered\_raw.csv` (4491행)

&#x20; - `all\_fingerprints.csv` (483행) — 또는 가공 자동화로 대체 가능



\---



\## 🚀 1단계: 스키마 + 시드 데이터 한 번에 실행



\### 진행



1\. MySQL Workbench 실행 → MySQL 서버 접속

2\. 새 쿼리 탭 열기 (`Ctrl + T`)

3\. `scripts/subway\_nav\_full.sql` 파일 내용 통째로 복사 → 쿼리 탭에 붙여넣기

4\. 번개 ⚡ 아이콘 클릭 (또는 `Ctrl + Shift + Enter`)



→ 5개 테이블 생성 + nodes 11개 + node\_edges 20개 + node\_directions 20개 자동 INSERT



\### 확인



```sql

USE subway\_nav;

SELECT 'nodes' AS tbl, COUNT(\*) AS cnt FROM nodes

UNION ALL SELECT 'node\_edges',      COUNT(\*) FROM node\_edges

UNION ALL SELECT 'node\_directions', COUNT(\*) FROM node\_directions;

```



기대 결과:



| tbl | cnt |

|---|---|

| nodes | 11 |

| node\_edges | 20 |

| node\_directions | 20 |



→ 다 나오면 OK. raw\_measurements / fingerprints 는 다음 단계.



\---



\## 🚀 2단계: raw\_measurements 임포트 (4491행)



CSV 파일을 MySQL Workbench의 Import Wizard로 적재합니다.



\### 진행



1\. 좌측 SCHEMAS 패널에서 `subway\_nav` 펼치기

2\. `Tables` 펼치고 → \*\*`raw\_measurements`\*\* 우클릭

3\. \*\*`Table Data Import Wizard`\*\* 클릭

4\. \*\*`Browse...`\*\* → `all\_filtered\_raw.csv` 파일 선택 → \*\*Next\*\*

5\. `Use existing table` 확인 → \*\*Next\*\*

6\. 컬럼 매핑 확인 (8개 컬럼 자동 ✓ 체크, `id`는 매핑 안 됨)

7\. \*\*Next\*\* → ⏰ \*\*1\~3분 기다리기\*\* → \*\*Finish\*\*



\### 확인



```sql

SELECT COUNT(\*) FROM raw\_measurements;

```



→ `4491` 나와야 함.



\---



\## 🚀 3단계: fingerprints 채우기 — 2가지 시나리오



\### 시나리오 A: 이미 가공된 CSV가 있을 때 (`all\_fingerprints.csv` 보유)



1\. `fingerprints` 우클릭 → \*\*`Table Data Import Wizard`\*\*

2\. `all\_fingerprints.csv` 선택 → \*\*Next\*\*

3\. `Use existing table` → \*\*Next\*\*

4\. ⚠️ \*\*중요!\*\* "Configure Import Settings" 화면에서 \*\*`node\_order` 체크 해제\*\*

5\. \*\*Next\*\* → 진행 → \*\*Finish\*\*



\### 시나리오 B: raw 데이터만 있을 때 ⭐ (가공 자동화)



`subway\_nav\_full.sql` 의 \*\*섹션 3 (가공 자동화)\*\* 부분만 다시 실행:



```sql

USE subway\_nav;



TRUNCATE TABLE fingerprints;



INSERT INTO fingerprints (

&#x20;   location, mac, ssid, frequency\_MHz, band,

&#x20;   rssi\_mean, rssi\_median, rssi\_std,

&#x20;   rssi\_min, rssi\_max, detect\_count, ap\_group

)

SELECT

&#x20;   location, mac,

&#x20;   MAX(ssid), MAX(frequency\_MHz),

&#x20;   CASE WHEN MAX(frequency\_MHz) < 3000 THEN '2.4GHz' ELSE '5GHz' END,

&#x20;   ROUND(AVG(rssi\_dBm), 2),

&#x20;   ROUND(AVG(rssi\_dBm), 2),

&#x20;   ROUND(STDDEV\_SAMP(rssi\_dBm), 2),

&#x20;   MIN(rssi\_dBm), MAX(rssi\_dBm),

&#x20;   COUNT(\*),

&#x20;   SUBSTRING(mac, 1, 14)

FROM raw\_measurements

WHERE location IS NOT NULL AND mac IS NOT NULL

GROUP BY location, mac;

```



> 💡 raw 데이터로부터 통계 자동 계산. 5/12 실측 데이터 기준 483행 생성됨.



\### 확인



```sql

SELECT COUNT(\*) FROM fingerprints;

```



→ `483` 나와야 함.



\---



\## ✅ 최종 검증



```sql

USE subway\_nav;



SELECT 'nodes'            AS tbl, COUNT(\*) AS cnt FROM nodes

UNION ALL SELECT 'node\_edges',       COUNT(\*) FROM node\_edges

UNION ALL SELECT 'node\_directions',  COUNT(\*) FROM node\_directions

UNION ALL SELECT 'raw\_measurements', COUNT(\*) FROM raw\_measurements

UNION ALL SELECT 'fingerprints',     COUNT(\*) FROM fingerprints;

```



\### 기대 결과



| tbl | cnt |

|---|---|

| nodes | 11 |

| node\_edges | 20 |

| node\_directions | 20 |

| raw\_measurements | 4491 |

| fingerprints | 483 |



→ \*\*DB 완성!\*\* 🎉



\---



\## 🧭 node\_directions 사용법 (앱 측 컨셉)



```

\[앱 워크플로우]

1\. KNN 으로 현재 위치 추정 → 예: "station\_exit"

2\. 다음 노드 (route 결과로) → 예: "floor1\_hall"

3\. 서버에 "station\_exit → floor1\_hall 방위각" 요청

4\. 서버 응답: heading\_degrees = 268 (W, 9시 방향)

5\. 앱이 스마트폰 나침반과 비교

&#x20;  - 폰이 268도 근처 향하면 → "이 방향 맞음" (강한 진동)

&#x20;  - 멀어지면 → 회전 안내

```



\### SQL 쿼리 예시



```sql

\-- "station\_exit → floor1\_hall" 방위각 조회

SELECT heading\_degrees, cardinal, clock\_position

FROM node\_directions

WHERE from\_node = 'station\_exit' AND to\_node = 'floor1\_hall';



\-- 결과: 268.0, 'W', 9

```



\### 양방향 데이터 의의



박경찬님이 양방향(예: A→B, B→A) 모두 측정한 이유:

\- 계단/분기점에서 양방향이 정확히 180도 차이 안 남

\- 5/20 검증: 직선 구간은 \~7° 오차, 계단/분기점은 30\~45° 차이

\- 180도 추정으로 했으면 계단 안내가 부정확했을 것

\- 본인 DB 는 측정값 그대로 보존



\---



\## 🔄 향후 데이터 수집 시나리오



새로 측정한 데이터를 추가할 때:



```

1\. 측정 도구가 raw CSV 생성

&#x20;  필수 컬럼: location, sample\_id, timestamp, mac, ssid, rssi\_dBm, frequency\_MHz



2\. raw\_measurements 테이블에 INSERT

&#x20;  (Import Wizard 또는 LOAD DATA INFILE)



3\. 위 3단계 시나리오 B 의 가공 SQL 실행

&#x20;  → fingerprints 자동 갱신



4\. Flask 서버 재시작

&#x20;  → KNN 이 새 학습 데이터로 다시 학습

```



손가공 없음. \*\*raw 데이터만 넣으면 끝.\*\*



\---



\## ⚠️ 자주 발생하는 에러



\### 에러 1: `'cp949' codec can't decode...`

\- \*\*원인:\*\* CSV의 한글을 윈도우가 못 읽음

\- \*\*해결:\*\* Configure Import Settings 에서 `Encoding`을 \*\*`utf-8`\*\* 로 변경



\### 에러 2: `Column 'ssid' specified twice` (fingerprints 임포트 중)

\- \*\*원인:\*\* `node\_order` 컬럼 잘못 매핑됨

\- \*\*해결:\*\* Configure 화면에서 `node\_order` 체크 해제



\### 에러 3: `Foreign key constraint fails`

\- \*\*원인:\*\* nodes 생성 안 하고 다른 테이블 먼저 시도

\- \*\*해결:\*\* 반드시 1단계부터 순서대로



\### 에러 4: `Can't create database 'subway\_nav'; database exists`

\- \*\*원인:\*\* 이미 같은 이름 DB가 있음

\- \*\*해결:\*\* Workbench에서 `subway\_nav` 우클릭 → `Drop Schema...` 로 삭제 후 재실행



\### 에러 5: `Check constraint 'node\_directions\_chk\_1' is violated` (node\_directions)

\- \*\*원인:\*\* `heading\_degrees` 값이 0\~360 범위 벗어남 또는 `clock\_position` 이 1\~12 범위 벗어남

\- \*\*해결:\*\* CSV 데이터에서 잘못된 값 찾아 수정



\### 에러 6: `'latin-1' codec can't encode characters` (서버 동작 중)

\- \*\*원인:\*\* MySQL root 비밀번호에 한글 포함

\- \*\*해결:\*\* MySQL Workbench 에서 비밀번호를 영문으로 변경 후 `.env` 파일도 갱신

&#x20; ```sql

&#x20; ALTER USER 'root'@'localhost' IDENTIFIED BY '영문비번';

&#x20; FLUSH PRIVILEGES;

&#x20; ```



\---



\## 📊 요약



```

☐ 1단계: subway\_nav\_full.sql 실행

&#x20;        → 5 테이블 + nodes(11) + node\_edges(20) + node\_directions(20) 자동 생성

☐ 2단계: raw\_measurements ← all\_filtered\_raw.csv (Import Wizard)

☐ 3단계: fingerprints 채우기

&#x20;        시나리오 A: all\_fingerprints.csv 임포트 (⚠️ node\_order 체크 해제!)

&#x20;        시나리오 B: 가공 SQL 1회 실행 (raw 데이터로부터 자동 생성) ⭐

☐ 검증: COUNT 쿼리로 11 / 20 / 20 / 4491 / 483 확인

```

