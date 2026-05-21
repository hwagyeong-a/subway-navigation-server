import json
from pathlib import Path

import pytest

from subway_server.api.errors import (
    InvalidNodeError,
    NoRouteError,
    NotConnectedError,
)
from subway_server.core.graph import (
    GraphData,
    assert_connected,
    dijkstra,
    load_graph,
)


FIXTURE_DIR = Path(__file__).parent.parent / "fixtures"


@pytest.fixture
def graph() -> GraphData:
    return load_graph(FIXTURE_DIR)


# -- load_graph -------------------------------------------------------


def test_load_graph_reads_all_three_files(graph):
    assert "station_exit" in graph.nodes
    assert graph.nodes["station_exit"].floor == "ground"
    assert ("station_exit", "floor1_hall") in graph.edge_lookup
    assert ("station_exit", "floor1_hall") in graph.directions


def test_load_graph_rejects_unknown_node_in_edges(tmp_path):
    (tmp_path / "nodes.json").write_text(json.dumps({
        "a": {"node_order": 1, "floor": "1F", "zone": "x", "description": ""}
    }))
    (tmp_path / "node_edges.json").write_text(json.dumps([
        {"from": "a", "to": "ghost", "edge_type": "flat"}
    ]))
    with pytest.raises(ValueError, match="unknown node"):
        load_graph(tmp_path)


def test_load_graph_rejects_asymmetric_edge(tmp_path):
    (tmp_path / "nodes.json").write_text(json.dumps({
        "a": {"node_order": 1, "floor": "1F", "zone": "x", "description": ""},
        "b": {"node_order": 2, "floor": "1F", "zone": "x", "description": ""},
    }))
    (tmp_path / "node_edges.json").write_text(json.dumps([
        {"from": "a", "to": "b", "edge_type": "flat"}
        # b → a 누락
    ]))
    with pytest.raises(ValueError, match="asymmetric"):
        load_graph(tmp_path)


def test_load_graph_rejects_direction_without_edge(tmp_path):
    (tmp_path / "nodes.json").write_text(json.dumps({
        "a": {"node_order": 1, "floor": "1F", "zone": "x", "description": ""},
        "b": {"node_order": 2, "floor": "1F", "zone": "x", "description": ""},
    }))
    (tmp_path / "node_edges.json").write_text("[]")
    (tmp_path / "node_directions.json").write_text(json.dumps([
        {"from": "a", "to": "b", "heading_degrees": 90, "cardinal": "E", "clock_position": 3}
    ]))
    with pytest.raises(ValueError, match="no matching edge"):
        load_graph(tmp_path)


def test_load_graph_missing_directions_file(tmp_path):
    (tmp_path / "nodes.json").write_text(json.dumps({
        "a": {"node_order": 1, "floor": "1F", "zone": "x", "description": ""}
    }))
    (tmp_path / "node_edges.json").write_text("[]")
    # node_directions.json 없음 → 빈 dict 로 처리
    g = load_graph(tmp_path)
    assert g.directions == {}


# -- dijkstra ---------------------------------------------------------


def test_dijkstra_simple_path(graph):
    path = dijkstra(graph, "station_exit", "floor1_hall")
    assert path == ["station_exit", "floor1_hall"]


def test_dijkstra_multi_hop(graph):
    path = dijkstra(graph, "station_exit", "b1_stairs")
    assert path[0] == "station_exit"
    assert path[-1] == "b1_stairs"
    assert "floor1_hall" in path
    assert "stairs_mid" in path


def test_dijkstra_invalid_from_raises(graph):
    with pytest.raises(InvalidNodeError):
        dijkstra(graph, "ghost", "floor1_hall")


def test_dijkstra_invalid_to_raises(graph):
    with pytest.raises(InvalidNodeError):
        dijkstra(graph, "station_exit", "ghost")


def test_dijkstra_same_node(graph):
    assert dijkstra(graph, "fare_gate", "fare_gate") == ["fare_gate"]


def test_dijkstra_no_route_for_isolated(graph):
    # isolated 노드는 edges 에 없음 → 도달 불가
    with pytest.raises(NoRouteError):
        dijkstra(graph, "station_exit", "isolated")


def test_dijkstra_cost_is_hop_count(graph):
    # station_exit → b1_stairs 의 경로 길이는 hop 수 기반
    path = dijkstra(graph, "station_exit", "b1_stairs")
    # 6노드 그래프에서 최단 경로 = 5 hops (station_exit→floor1_hall→fare_gate→floor1_stairs→stairs_mid→b1_stairs)
    assert len(path) == 6


# -- direction lookup -------------------------------------------------


def test_find_direction_returns_data(graph):
    d = graph.direction("station_exit", "floor1_hall")
    assert d is not None
    assert d.heading_degrees == 268
    assert d.cardinal == "W"
    assert d.clock_position == 9


def test_find_direction_returns_none_for_invalid(graph):
    assert graph.direction("station_exit", "ghost") is None


# -- edge lookup ------------------------------------------------------


def test_edge_lookup_flat(graph):
    e = graph.edge("station_exit", "floor1_hall")
    assert e is not None
    assert e.edge_type == "flat"


def test_edge_lookup_stairs(graph):
    e = graph.edge("stairs_mid", "b1_stairs")
    assert e is not None
    assert e.edge_type == "stairs"


def test_edge_lookup_returns_none_for_missing(graph):
    assert graph.edge("station_exit", "b1_stairs") is None


# -- assert_connected -------------------------------------------------


def test_assert_connected_adjacent(graph):
    assert_connected(graph, "station_exit", "floor1_hall")  # no exception


def test_assert_connected_not_adjacent(graph):
    with pytest.raises(NotConnectedError):
        assert_connected(graph, "station_exit", "b1_stairs")


def test_assert_connected_invalid_node(graph):
    with pytest.raises(InvalidNodeError):
        assert_connected(graph, "station_exit", "ghost")
