-- ============================================================
-- DB 적재 검증 쿼리
-- 모든 임포트가 끝난 뒤 실행해서 행 수 확인
-- ============================================================

USE subway_nav;

-- 전체 테이블 행 수
SELECT 'nodes'            AS tbl, COUNT(*) AS cnt FROM nodes
UNION ALL
SELECT 'node_edges',            COUNT(*) FROM node_edges
UNION ALL
SELECT 'raw_measurements',      COUNT(*) FROM raw_measurements
UNION ALL
SELECT 'fingerprints',          COUNT(*) FROM fingerprints;

-- 기대값:
--   nodes              11
--   node_edges         20
--   raw_measurements   4491
--   fingerprints       483

-- 노드별 fingerprint AP 수
SELECT location, COUNT(*) AS ap_count
FROM fingerprints
GROUP BY location
ORDER BY ap_count DESC;