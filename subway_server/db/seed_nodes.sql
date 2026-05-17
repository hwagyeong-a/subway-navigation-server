-- ============================================================
-- 노드 + 엣지 시드 데이터 (팀 B, 2026-05-15)
-- 전제: schema.sql 이 먼저 실행되어 있어야 함
-- raw_measurements, fingerprints 는 CSV 임포트로 채움
-- ============================================================

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