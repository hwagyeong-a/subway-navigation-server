-- ============================================================
-- subway_nav DB 전체 구축 + 가공 자동화 스크립트 (v3)
-- 팀 B - 2026-05-29 갱신
-- MySQL 8.0+
--
-- v3 변경 사항:
--   - floor1_hall 제거 (도착 전 인식 문제 해결, 역입구↔개찰구 직접 연결)
--   - stairs_mid 제거 (라이브 DB 반영분, b1_stairs↔floor1_stairs 직접 연결)
--
-- v2 변경 사항 (박경찬님 방위각 데이터 반영):
--   - node_directions 테이블 추가
-- ============================================================

CREATE DATABASE subway_nav CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE subway_nav;


-- ============================================================
-- 1. 테이블 5개 생성
-- ============================================================

CREATE TABLE nodes (
    node_id     INT PRIMARY KEY,
    location    VARCHAR(64)  NOT NULL UNIQUE,
    node_order  INT          NOT NULL,
    floor       VARCHAR(16),
    zone        VARCHAR(32),
    description VARCHAR(255)
);
CREATE INDEX idx_nodes_location ON nodes(location);

CREATE TABLE node_edges (
    from_node  VARCHAR(64) NOT NULL,
    to_node    VARCHAR(64) NOT NULL,
    edge_type  VARCHAR(16) NOT NULL DEFAULT 'flat',
    PRIMARY KEY (from_node, to_node),
    FOREIGN KEY (from_node) REFERENCES nodes(location),
    FOREIGN KEY (to_node)   REFERENCES nodes(location)
);
CREATE INDEX idx_edges_from ON node_edges(from_node);

CREATE TABLE node_directions (
    from_node        VARCHAR(64)  NOT NULL,
    to_node          VARCHAR(64)  NOT NULL,
    heading_degrees  DECIMAL(5,1) NOT NULL,
    cardinal         VARCHAR(2),
    clock_position   INT,
    PRIMARY KEY (from_node, to_node),
    FOREIGN KEY (from_node) REFERENCES nodes(location),
    FOREIGN KEY (to_node)   REFERENCES nodes(location),
    CHECK (heading_degrees >= 0 AND heading_degrees < 360),
    CHECK (clock_position BETWEEN 1 AND 12)
);
CREATE INDEX idx_dir_from ON node_directions(from_node);

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


-- ============================================================
-- 2. 시드 데이터 (floor1_hall, stairs_mid 제거됨)
-- ============================================================

INSERT INTO nodes (node_id, location, node_order, floor, zone, description) VALUES
(1,  'station_exit',          1,  'ground', 'entrance', '역 지상 출입구'),
(3,  'fare_gate',              3,  '1F',     'gate',     '개찰구'),
(4,  'floor1_stairs',          4,  '1F',     'stairs',   '1층 계단 시작'),
(6,  'b1_stairs',              6,  'B1',     'stairs',   '지하 계단'),
(7,  'b1_elevator',            7,  'B1',     'hall',     '지하 엘리베이터 앞'),
(8,  'b1_down_stairs_front',   8,  'B1',     'branch',   '지하 하행 계단 앞 (3방향 분기)'),
(9,  'down_platform',          9,  'B1',     'platform', '하행 승강장'),
(10, 'b1_up_stairs_front',     10, 'B1',     'stairs',   '지하 상행 계단 앞'),
(11, 'up_platform',            11, 'B1',     'platform', '상행 승강장');

INSERT INTO node_edges (from_node, to_node, edge_type) VALUES
('b1_down_stairs_front',  'b1_elevator',           'flat'),
('b1_down_stairs_front',  'b1_up_stairs_front',    'branch'),
('b1_down_stairs_front',  'down_platform',         'branch'),
('b1_elevator',           'b1_down_stairs_front',  'flat'),
('b1_elevator',           'b1_stairs',             'flat'),
('b1_stairs',             'b1_elevator',           'flat'),
('b1_stairs',             'floor1_stairs',         'stairs'),
('b1_up_stairs_front',    'b1_down_stairs_front',  'branch'),
('b1_up_stairs_front',    'up_platform',           'stairs'),
('down_platform',         'b1_down_stairs_front',  'branch'),
('fare_gate',             'floor1_stairs',         'flat'),
('fare_gate',             'station_exit',          'flat'),
('floor1_stairs',         'b1_stairs',             'stairs'),
('floor1_stairs',         'fare_gate',             'flat'),
('station_exit',          'fare_gate',             'flat'),
('up_platform',           'b1_up_stairs_front',    'stairs');

INSERT INTO node_directions (from_node, to_node, heading_degrees, cardinal, clock_position) VALUES
('b1_down_stairs_front',  'b1_elevator',           30,  'NE', 1),
('b1_down_stairs_front',  'b1_up_stairs_front',    255, 'W',  8),
('b1_down_stairs_front',  'down_platform',         168, 'S',  6),
('b1_elevator',           'b1_down_stairs_front',  255, 'W',  8),
('b1_elevator',           'b1_stairs',             347, 'N',  12),
('b1_stairs',             'b1_elevator',           180, 'S',  6),
('b1_stairs',             'floor1_stairs',         323, 'NW', 11),
('b1_up_stairs_front',    'b1_down_stairs_front',  30,  'NE', 1),
('b1_up_stairs_front',    'up_platform',           195, 'S',  6),
('down_platform',         'b1_down_stairs_front',  328, 'NW', 11),
('fare_gate',             'floor1_stairs',         324, 'NW', 11),
('fare_gate',             'station_exit',          81,  'E',  3),
('floor1_stairs',         'b1_stairs',             182, 'S',  6),
('floor1_stairs',         'fare_gate',             171, 'S',  6),
('station_exit',          'fare_gate',             268, 'W',  9),
('up_platform',           'b1_up_stairs_front',    330, 'NW', 11);


-- ============================================================
-- 3. 가공 자동화 — raw_measurements → fingerprints
-- ============================================================

TRUNCATE TABLE fingerprints;

INSERT INTO fingerprints (
    location, mac, ssid, frequency_MHz, band,
    rssi_mean, rssi_median, rssi_std,
    rssi_min, rssi_max, detect_count, ap_group
)
SELECT
    location, mac,
    MAX(ssid), MAX(frequency_MHz),
    CASE WHEN MAX(frequency_MHz) < 3000 THEN '2.4GHz' ELSE '5GHz' END,
    ROUND(AVG(rssi_dBm), 2),
    ROUND(AVG(rssi_dBm), 2),
    ROUND(STDDEV_SAMP(rssi_dBm), 2),
    MIN(rssi_dBm), MAX(rssi_dBm),
    COUNT(*),
    SUBSTRING(mac, 1, 14)
FROM raw_measurements
WHERE location IS NOT NULL AND mac IS NOT NULL
GROUP BY location, mac;


-- ============================================================
-- 4. 검증
-- ============================================================

SELECT 'nodes' AS tbl, COUNT(*) AS cnt FROM nodes
UNION ALL SELECT 'node_edges',       COUNT(*) FROM node_edges
UNION ALL SELECT 'node_directions',  COUNT(*) FROM node_directions
UNION ALL SELECT 'raw_measurements', COUNT(*) FROM raw_measurements
UNION ALL SELECT 'fingerprints',     COUNT(*) FROM fingerprints;