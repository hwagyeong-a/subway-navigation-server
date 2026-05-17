-- ============================================================
-- WiFi 측위 시스템 DB 스키마 (MySQL 8.0+)
-- 팀 B - 2026-05-15 갱신
-- ============================================================

-- 클린 빌드 (개발 환경에서만!)
DROP DATABASE IF EXISTS subway_nav;
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