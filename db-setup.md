# subway_nav DB 구축 매뉴얼

> 다른 PC에서 같은 DB를 재현하려면 이 매뉴얼을 따라 하세요.
> 본인 PC 기준 약 10~15분 소요.

## 📦 준비물

- **MySQL 8.0 이상** 설치
- **MySQL Workbench** (관리 도구)
- 팀에서 받은 **CSV 파일 2개**:
  - `all_filtered_raw.csv` (4491행)
  - `all_fingerprints.csv` (483행)

---

## 🚀 1단계: 스키마 + 시드 데이터 생성

GitHub 저장소에서 `subway_nav.sql` 파일을 받아서 실행합니다.

### 진행

1. MySQL Workbench 실행 → MySQL 서버 접속
2. 새 쿼리 탭 열기 (`Ctrl + T`)
3. GitHub에서 `subway_nav.sql` 내용 통째로 복사
4. 쿼리 탭에 붙여넣기
5. 번개 ⚡ 아이콘 클릭 (또는 `Ctrl + Shift + Enter`)

### 확인

```sql
USE subway_nav;
SELECT 'nodes' AS tbl, COUNT(*) AS cnt FROM nodes
UNION ALL SELECT 'node_edges', COUNT(*) FROM node_edges;
```

기대 결과:

| tbl | cnt |
|---|---|
| nodes | 11 |
| node_edges | 20 |

→ 11, 20 나오면 OK. 다음 단계로.

---

## 🚀 2단계: raw_measurements 임포트 (4491행)

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

## 🚀 3단계: fingerprints 임포트 (483행)

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
- **해결:** 위 3단계 4번처럼 `node_order` 체크 해제

### 에러 3: `Foreign key constraint fails`

- **원인:** 1단계(nodes 생성) 안 하고 2, 3단계 먼저 시도
- **해결:** 반드시 1단계부터 순서대로

### 에러 4: `Can't create database 'subway_nav'; database exists`

- **원인:** 이미 같은 이름 DB가 있음
- **해결:** Workbench에서 좌측 `subway_nav` 우클릭 → `Drop Schema...` 로 삭제 후 재실행

---

## 📊 요약 — 한눈에 보기

```
☐ 1단계: subway_nav.sql 실행
   └─ nodes (11) + node_edges (20) 자동 생성

☐ 2단계: raw_measurements ← all_filtered_raw.csv
   └─ Import Wizard, 1~3분 소요

☐ 3단계: fingerprints ← all_fingerprints.csv
   └─ Import Wizard, ⚠️ node_order 체크 해제!

☐ 검증: COUNT 쿼리로 11 / 20 / 4491 / 483 확인
```
