# subway_nav DB 구축 매뉴얼

> 다른 PC에서 같은 DB를 재현하려면 이 매뉴얼을 따라 하세요.
> 처음 시도 시 약 30분~1시간, 익숙해지면 15분 정도 소요됩니다.
> (에러 발생 시 ⚠️ 자주 발생하는 에러 섹션 참고)

## 📦 준비물

- **MySQL 8.0 이상** 설치
- **MySQL Workbench** (관리 도구)
- 팀에서 받은 **CSV 파일 2개**:
  - `all_filtered_raw.csv` (4491행)
  - `all_fingerprints.csv` (483행)

---

## 🚀 1단계: 스키마 생성 (4개 테이블)

### 진행

1. MySQL Workbench 실행 → MySQL 서버 접속
2. 새 쿼리 탭 열기 (`Ctrl + T`)
3. 아래 SQL을 통째로 복사해서 쿼리 탭에 붙여넣기
4. 번개 ⚡ 아이콘 클릭 (또는 `Ctrl + Shift + Enter`)

```sql
-- ============================================================
-- WiFi 측위 시스템 DB 스키마 (MySQL 8.0+)
-- ============================================================

CREATE DATABASE subway_nav CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE subway_nav;

-- 1. 노드 마스터
CREATE TABLE nodes (
    node_id     INT PRIMARY KEY,
    location    VARCHAR(64)  NOT NULL UNIQUE,
    node_order  INT          NOT NULL,
    floor       VARCHAR(16),
    zone        VARCHAR(32),
    description VARCHAR(255)
);
CREATE INDEX idx_nodes_location ON nodes(location);

-- 2. 노드 인접 관계 (양방향)
CREATE TABLE node_edges (
    from_node  VARCHAR(64) NOT NULL,
    to_node    VARCHAR(64) NOT NULL,
    edge_type  VARCHAR(16) NOT NULL DEFAULT 'flat',
    PRIMARY KEY (from_node, to_node),
    FOREIGN KEY (from_node) REFERENCES nodes(location),
    FOREIGN KEY (to_node)   REFERENCES nodes(location)
);
CREATE INDEX idx_edges_from ON node_edges(from_node);

-- 3. 원본 측정 데이터
CREATE TABLE raw_measurements (
    id            BIGINT AUTO_INCREMENT PRIMARY KEY,
    location      VARCHAR(64) NOT NULL,
    node_order    INT,
    sample_id     INT         NOT NULL,
    timestamp     TIMESTAMP   NOT NULL,
    mac           VARCHAR(17) NOT NULL,
    ssid          VARCHAR(64),
    rssi_dBm      INT         NOT NULL,
    frequency_MHz INT         NOT NULL,
    FOREIGN KEY (location) REFERENCES nodes(location)
);
CREATE INDEX idx_raw_location ON raw_measurements(location);
CREATE INDEX idx_raw_mac      ON raw_measurements(mac);

-- 4. Fingerprint (KNN 학습용)
CREATE TABLE fingerprints (
    location      VARCHAR(64)    NOT NULL,
    mac           VARCHAR(17)    NOT NULL,
    ssid          VARCHAR(64),
    frequency_MHz INT,
    band          VARCHAR(8),
    rssi_mean     DECIMAL(6, 2)  NOT NULL,
    rssi_median   DECIMAL(6, 2),
    rssi_std      DECIMAL(6, 2),
    rssi_min      INT,
    rssi_max      INT,
    detect_count  INT            NOT NULL,
    ap_group      VARCHAR(14),
    PRIMARY KEY (location, mac),
    FOREIGN KEY (location) REFERENCES nodes(location)
);
CREATE INDEX idx_fp_location ON fingerprints(location);
CREATE INDEX idx_fp_mac      ON fingerprints(mac);
```

### 확인

```sql
USE subway_nav;
SHOW TABLES;
```

→ 4개 테이블 (`fingerprints`, `node_edges`, `nodes`, `raw_measurements`) 나오면 OK.

---

## 🚀 2단계: nodes + node_edges 시드 데이터 INSERT

한글 description 때문에 Import Wizard가 에러를 내므로 SQL 직접 INSERT로 진행합니다.

### 진행

새 쿼리 탭에서 아래 SQL 통째로 실행:

```sql
USE subway_nav;

-- 11개 노드
INSERT INTO nodes (node_id, location, node_order, floor, zone, description) VALUES
(1,  'station_exit',          1,  'ground', 'entrance', '역 지상 출입구'),
(2,  'fare_gate',              2,  '1F',     'gate',     '개찰구'),
(3,  'floor1_hall',            3,  '1F',     'hall',     '1층 홀'),
(4,  'floor1_stairs',          4,  '1F',     'stairs',   '1층 계단 시작'),
(5,  'stairs_mid',             5,  'mid',    'stairs',   '층 사이 계단 중앙'),
(6,  'b1_stairs',              6,  'B1',     'stairs',   '지하 계단'),
(7,  'b1_elevator',            7,  'B1',     'hall',     '지하 엘리베이터 앞'),
(8,  'b1_down_stairs_front',   8,  'B1',     'branch',   '지하 하행 계단 앞 (분기점)'),
(9,  'down_platform',          9,  'B1',     'platform', '하행 승강장'),
(10, 'b1_up_stairs_front',     10, 'B1',     'stairs',   '지하 상행 계단 앞'),
(11, 'up_platform',            11, 'B1',     'platform', '상행 승강장');

-- 20개 엣지 (양방향)
INSERT INTO node_edges (from_node, to_node, edge_type) VALUES
('b1_down_stairs_front',  'b1_elevator',           'flat'),
('b1_down_stairs_front',  'b1_up_stairs_front',    'branch'),
('b1_down_stairs_front',  'down_platform',         'branch'),
('b1_elevator',           'b1_down_stairs_front',  'flat'),
('b1_elevator',           'b1_stairs',             'flat'),
('b1_stairs',             'b1_elevator',           'flat'),
('b1_stairs',             'stairs_mid',            'stairs'),
('b1_up_stairs_front',    'b1_down_stairs_front',  'branch'),
('b1_up_stairs_front',    'up_platform',           'stairs'),
('down_platform',         'b1_down_stairs_front',  'branch'),
('fare_gate',             'floor1_hall',           'flat'),
('fare_gate',             'station_exit',          'flat'),
('floor1_hall',           'fare_gate',             'flat'),
('floor1_hall',           'floor1_stairs',         'flat'),
('floor1_stairs',         'floor1_hall',           'flat'),
('floor1_stairs',         'stairs_mid',            'stairs'),
('stairs_mid',            'b1_stairs',             'stairs'),
('stairs_mid',            'floor1_stairs',         'stairs'),
('station_exit',          'fare_gate',             'flat'),
('up_platform',           'b1_up_stairs_front',    'stairs');
```

### 확인

```sql
SELECT 'nodes' AS tbl, COUNT(*) AS cnt FROM nodes
UNION ALL SELECT 'node_edges', COUNT(*) FROM node_edges;
```

기대 결과:

| tbl | cnt |
|---|---|
| nodes | 11 |
| node_edges | 20 |

---

## 🚀 3단계: raw_measurements 임포트 (4491행)

CSV 파일을 MySQL Workbench의 Import Wizard로 적재합니다.

### 진행

1. 좌측 SCHEMAS 패널에서 `subway_nav` 펼치기
2. `Tables` 펼치고 → **`raw_measurements`** 우클릭
3. **`Table Data Import Wizard`** 클릭
4. **`Browse...`** → `all_filtered_raw.csv` 파일 선택
5. **Next**
6. "Select Destination" 화면
   - `Use existing table` 선택 (기본값)
   - 테이블: `subway_nav.raw_measurements` 확인
   - **Next**
7. "Configure Import Settings" 화면
   - 컬럼 매핑이 자동으로 잡힘
   - 다음 8개 컬럼이 ✓ 체크되어야 함:

   ```
   ✓ location        → location
   ✓ node_order      → node_order
   ✓ sample_id       → sample_id
   ✓ timestamp       → timestamp
   ✓ mac             → mac
   ✓ ssid            → ssid
   ✓ rssi_dBm        → rssi_dBm
   ✓ frequency_MHz   → frequency_MHz
   ```

   - **`id`는 매핑 안 됨 = 정상** (AUTO_INCREMENT)
   - **Next**
8. "Import Data" 화면 → **Next**
9. ⏰ **1~3분 기다리기** (4491행이라 시간 걸림)
10. **"4491 records imported"** 메시지 확인 → **Finish**

### 확인

```sql
SELECT COUNT(*) FROM raw_measurements;
```

→ `4491` 나와야 함.

---

## 🚀 4단계: fingerprints 임포트 (483행)

### 진행

1. `fingerprints` 우클릭 → **`Table Data Import Wizard`**
2. `Browse...` → `all_fingerprints.csv` 선택 → **Next**
3. `Use existing table` → **Next**
4. "Configure Import Settings" 화면 ⚠️ **중요!**
   - CSV에는 `node_order` 컬럼이 있는데 **fingerprints 테이블엔 없습니다**
   - **`node_order` 줄의 ✓ 체크 해제** 필요
   - 안 그러면 `Column 'ssid' specified twice` 에러 발생
   - 나머지 12개 컬럼은 ✓ 유지:

   ```
   ✓ location, mac, ssid, frequency_MHz, rssi_mean,
   ✓ rssi_median, rssi_std, rssi_min, rssi_max,
   ✓ detect_count, ap_group, band
   ✗ node_order  ← 체크 해제!
   ```

   - **Next**
5. **Next** → 진행 → **Finish**

### 확인

```sql
SELECT COUNT(*) FROM fingerprints;
```

→ `483` 나와야 함.

---

## ✅ 최종 검증

모든 단계 끝나면 다음 SQL로 한 번에 확인:

```sql
USE subway_nav;

SELECT 'nodes'            AS tbl, COUNT(*) AS cnt FROM nodes
UNION ALL SELECT 'node_edges',       COUNT(*) FROM node_edges
UNION ALL SELECT 'raw_measurements', COUNT(*) FROM raw_measurements
UNION ALL SELECT 'fingerprints',     COUNT(*) FROM fingerprints;
```

### 기대 결과

| tbl | cnt |
|---|---|
| nodes | 11 |
| node_edges | 20 |
| raw_measurements | 4491 |
| fingerprints | 483 |

→ 이 숫자 그대로 나오면 **DB 완성!** 🎉

---

## ⚠️ 자주 발생하는 에러

### 에러 1: `'cp949' codec can't decode...` (raw_measurements 임포트 중)

- **원인:** CSV의 한글 SSID를 윈도우가 못 읽음
- **해결:** Configure Import Settings 화면에서 `Encoding`을 **`utf-8`** 로 변경

### 에러 2: `Column 'ssid' specified twice` (fingerprints 임포트 중)

- **원인:** `node_order` 컬럼이 잘못 매핑됨
- **해결:** 위 4단계 4번처럼 `node_order` 체크 해제

### 에러 3: `Foreign key constraint fails`

- **원인:** 1, 2단계(nodes 생성) 안 하고 3, 4단계 먼저 시도
- **해결:** 반드시 1단계부터 순서대로

### 에러 4: `Can't create database 'subway_nav'; database exists`

- **원인:** 이미 같은 이름 DB가 있음
- **해결:** Workbench에서 좌측 `subway_nav` 우클릭 → `Drop Schema...` 로 삭제 후 재실행

---

## 📊 요약 — 한눈에 보기

```
☐ 1단계: 스키마 SQL 실행 → 4개 빈 테이블 생성
☐ 2단계: nodes + node_edges INSERT SQL 실행 → 11, 20행
☐ 3단계: raw_measurements ← all_filtered_raw.csv (Import Wizard)
☐ 4단계: fingerprints ← all_fingerprints.csv (⚠️ node_order 체크 해제!)
☐ 검증: COUNT 쿼리로 11 / 20 / 4491 / 483 확인
```
