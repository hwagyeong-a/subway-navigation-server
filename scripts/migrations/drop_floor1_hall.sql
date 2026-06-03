-- =============================================================================
-- 1층홀(floor1_hall) 노드 제거 마이그레이션
-- =============================================================================
-- 작성: 김화경 | 2026-05-28
--
-- 배경:
--   지하철역 노드 간격이 너무 짧아, 실제 1층홀 위치에 도착하기 전에
--   측위가 "1층홀 도착"으로 인식되는 문제 발생.
--   → "역입구 → 개찰구" 직접 연결로 노드 간격을 넓혀 측위 타이밍 개선.
--
-- 영향:
--   - 노드 수:    11 → 10
--   - 엣지 수:    20 → 18 (1층홀 관련 4개 삭제 + 역입구↔개찰구 2개 추가)
--   - 방위각 수:  20 → 18 (동일 패턴)
--   - raw 측정:   4491 → 3969 (1층홀 522개 삭제)
--   - fingerprints: 483 → 426 (1층홀 57개 삭제)
--
-- 역입구 ↔ 개찰구 새 방위각:
--   - 역입구 → 개찰구:  268° (W, 9시) — 기존 역입구→1층홀과 동일 방향
--   - 개찰구 → 역입구:  81°  (E, 3시) — 기존 1층홀→역입구와 동일 방향
--   - 1층홀이 두 노드 사이에 있었으므로 같은 통로 방향으로 가정.
--
-- 사용법:
--   mysql -u root -p subway_nav < drop_floor1_hall.sql
--   또는 MySQL 콘솔에서: source drop_floor1_hall.sql;
-- =============================================================================

USE subway_nav;

-- 안전: 트랜잭션 시작. 결과 이상하면 ROLLBACK 가능.
START TRANSACTION;

-- 1. 1층홀 관련 엣지 4개 삭제
--    (역입구↔1층홀, 1층홀↔개찰구 각 양방향)
DELETE FROM node_edges
WHERE from_node = 'floor1_hall' OR to_node = 'floor1_hall';

-- 2. 1층홀 관련 방위각 4개 삭제
DELETE FROM node_directions
WHERE from_node = 'floor1_hall' OR to_node = 'floor1_hall';

-- 3. 역입구 ↔ 개찰구 새 직접 엣지 추가 (양방향)
INSERT INTO node_edges (from_node, to_node, edge_type) VALUES
    ('station_exit', 'fare_gate',    'flat'),
    ('fare_gate',    'station_exit', 'flat');

-- 4. 역입구 ↔ 개찰구 새 방위각 추가
INSERT INTO node_directions (from_node, to_node, heading_degrees, cardinal, clock_position) VALUES
    ('station_exit', 'fare_gate',    268, 'W', 9),
    ('fare_gate',    'station_exit', 81,  'E', 3);

-- 5. 1층홀 raw 측정 데이터 삭제 (522개)
DELETE FROM raw_measurements WHERE location = 'floor1_hall';

-- 6. 1층홀 fingerprints 평균값 삭제 (57개)
DELETE FROM fingerprints WHERE location = 'floor1_hall';

-- 7. 1층홀 노드 자체 삭제 (마지막)
DELETE FROM nodes WHERE location = 'floor1_hall';

-- 결과 확인
SELECT 'nodes'             AS tbl, COUNT(*) AS cnt FROM nodes
UNION ALL SELECT 'node_edges',       COUNT(*) FROM node_edges
UNION ALL SELECT 'node_directions',  COUNT(*) FROM node_directions
UNION ALL SELECT 'raw_measurements', COUNT(*) FROM raw_measurements
UNION ALL SELECT 'fingerprints',     COUNT(*) FROM fingerprints;

-- 기대값:
--   nodes              10
--   node_edges         18
--   node_directions    18
--   raw_measurements   3969
--   fingerprints       426

-- 위 결과가 맞으면 COMMIT, 다르면 ROLLBACK
-- COMMIT 은 수동으로 실행 (안전을 위해 자동 처리 안 함):
--   COMMIT;
-- 되돌리려면:
--   ROLLBACK;