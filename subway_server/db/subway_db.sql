-- ============================================
-- 서버 DB 초기 세팅
-- ============================================

-- 1. 데이터베이스 생성 및 선택
CREATE DATABASE subway_nav;
USE subway_nav;

-- 2. Wi-Fi fingerprint 테이블 생성
CREATE TABLE fingerprint (
    -- 각 데이터의 고유 번호
    id INT AUTO_INCREMENT PRIMARY KEY,
    -- 현재 위치 노드 이름 (예: A, B, C)
    node_id VARCHAR(10) NOT NULL,
    -- Wi-Fi 공유기 고유 주소 (MAC 주소 형식: aa:bb:cc:dd:ee:ff, 17자 고정)
    bssid VARCHAR(17) NOT NULL,
    -- Wi-Fi 신호 세기 (보통 음수. 예: -55, -70)
    rssi INT NOT NULL
);

-- 3. 조회 성능용 인덱스
CREATE INDEX idx_fp_node ON fingerprint(node_id);
CREATE INDEX idx_fp_bssid ON fingerprint(bssid);

-- 4. 테스트용 fingerprint 데이터
--    노드별로 신호 패턴이 다르게 들어가야 KNN이 의미있게 동작함.
INSERT INTO fingerprint (node_id, bssid, rssi) VALUES
    -- A 노드: AP1이 강함
    ('A', 'aa:bb:cc:dd:ee:01', -45),
    ('A', 'aa:bb:cc:dd:ee:02', -75),
    ('A', 'aa:bb:cc:dd:ee:03', -80),
    -- B 노드: AP2가 강함
    ('B', 'aa:bb:cc:dd:ee:01', -78),
    ('B', 'aa:bb:cc:dd:ee:02', -42),
    ('B', 'aa:bb:cc:dd:ee:03', -76),
    -- C 노드: AP3이 강함
    ('C', 'aa:bb:cc:dd:ee:01', -82),
    ('C', 'aa:bb:cc:dd:ee:02', -77),
    ('C', 'aa:bb:cc:dd:ee:03', -48);

-- ============================================
-- 검증용 쿼리 (실행 결과 눈으로 확인)
-- ============================================

-- 5. 데이터 잘 들어갔는지 전체 조회
SELECT * FROM fingerprint;

-- 6. 노드별 샘플 수 확인 (각각 3개씩 나와야 함)
SELECT node_id, COUNT(*) AS samples
FROM fingerprint
GROUP BY node_id;

-- 7. 인덱스 3개 모두 만들어졌는지 확인
SHOW INDEX FROM fingerprint;