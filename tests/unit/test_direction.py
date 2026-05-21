"""GraphData.direction() 조회 동작 검증.

원본 명세의 좌표계 컨벤션(정북=0°, 시계방향)은 박경찬 실측 데이터의 cardinal/clock_position
필드를 통해 간접 검증된다 — 별도 atan2 변환 로직 없이 DB 조회만으로 결과 반환.
"""

from pathlib import Path

import pytest

from subway_server.core.graph import GraphData, load_graph


FIXTURE_DIR = Path(__file__).parent.parent / "fixtures"


@pytest.fixture
def graph() -> GraphData:
    return load_graph(FIXTURE_DIR)


def test_find_direction_basic(graph):
    d = graph.direction("station_exit", "floor1_hall")
    assert d is not None
    assert d.heading_degrees == 268


def test_find_direction_returns_cardinal(graph):
    d = graph.direction("station_exit", "floor1_hall")
    assert d.cardinal == "W"


def test_find_direction_returns_clock(graph):
    d = graph.direction("station_exit", "floor1_hall")
    assert d.clock_position == 9


def test_find_direction_reverse_direction(graph):
    d = graph.direction("floor1_hall", "station_exit")
    assert d is not None
    assert d.heading_degrees == 81
    assert d.cardinal == "E"


def test_find_direction_stairs_node(graph):
    # 계단 사이의 양방향 확인
    d_up = graph.direction("floor1_stairs", "stairs_mid")
    d_down = graph.direction("stairs_mid", "floor1_stairs")
    assert d_up is not None and d_up.heading_degrees == 321
    assert d_down is not None and d_down.heading_degrees == 182


def test_find_direction_missing_pair_returns_none(graph):
    # 직접 연결되지 않은 노드 쌍
    assert graph.direction("station_exit", "b1_stairs") is None


def test_directions_have_valid_heading_range(graph):
    # 0 ≤ heading_degrees < 360
    for d in graph.directions.values():
        assert 0 <= d.heading_degrees < 360
