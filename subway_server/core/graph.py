import heapq
import json
from dataclasses import dataclass
from pathlib import Path

from ..api.errors import (
    InvalidNodeError,
    NoRouteError,
    NotConnectedError,
)


@dataclass(frozen=True)
class NodeMeta:
    node_order: int
    floor: str
    zone: str
    description: str


@dataclass(frozen=True)
class Edge:
    from_node: str
    to_node: str
    edge_type: str  # "flat" | "stairs" | "branch"


@dataclass(frozen=True)
class Direction:
    from_node: str
    to_node: str
    heading_degrees: float
    cardinal: str
    clock_position: int


@dataclass(frozen=True)
class GraphData:
    nodes: dict[str, NodeMeta]
    adjacency: dict[str, list[str]]
    edge_lookup: dict[tuple[str, str], Edge]
    directions: dict[tuple[str, str], Direction]

    def has_node(self, node_id: str) -> bool:
        return node_id in self.nodes

    def neighbors(self, node_id: str) -> list[str]:
        return self.adjacency.get(node_id, [])

    def is_connected(self, a: str, b: str) -> bool:
        return (a, b) in self.edge_lookup

    def edge(self, a: str, b: str) -> Edge | None:
        return self.edge_lookup.get((a, b))

    def direction(self, a: str, b: str) -> Direction | None:
        return self.directions.get((a, b))

    def meta(self, node_id: str) -> NodeMeta:
        return self.nodes[node_id]


def load_graph(data_dir: Path | str) -> GraphData:
    data_dir = Path(data_dir)
    nodes_raw = json.loads((data_dir / "nodes.json").read_text(encoding="utf-8"))
    edges_raw = json.loads((data_dir / "node_edges.json").read_text(encoding="utf-8"))

    directions_path = data_dir / "node_directions.json"
    if directions_path.exists():
        directions_raw = json.loads(directions_path.read_text(encoding="utf-8"))
    else:
        directions_raw = []

    nodes: dict[str, NodeMeta] = {}
    for nid, meta in nodes_raw.items():
        nodes[nid] = NodeMeta(
            node_order=int(meta["node_order"]),
            floor=str(meta.get("floor", "")),
            zone=str(meta.get("zone", "")),
            description=str(meta.get("description", "")),
        )

    edge_lookup: dict[tuple[str, str], Edge] = {}
    adjacency: dict[str, list[str]] = {nid: [] for nid in nodes}
    for raw in edges_raw:
        e = Edge(from_node=raw["from"], to_node=raw["to"], edge_type=raw["edge_type"])
        edge_lookup[(e.from_node, e.to_node)] = e
        adjacency.setdefault(e.from_node, []).append(e.to_node)

    directions: dict[tuple[str, str], Direction] = {}
    for raw in directions_raw:
        d = Direction(
            from_node=raw["from"],
            to_node=raw["to"],
            heading_degrees=float(raw["heading_degrees"]),
            cardinal=str(raw["cardinal"]),
            clock_position=int(raw["clock_position"]),
        )
        directions[(d.from_node, d.to_node)] = d

    _validate_graph(nodes, edge_lookup, directions)

    return GraphData(
        nodes=nodes,
        adjacency=adjacency,
        edge_lookup=edge_lookup,
        directions=directions,
    )


def _validate_graph(
    nodes: dict[str, NodeMeta],
    edge_lookup: dict[tuple[str, str], Edge],
    directions: dict[tuple[str, str], Direction],
) -> None:
    """Surface data bugs early. Does not auto-fix."""
    for (a, b), _edge in edge_lookup.items():
        if a not in nodes:
            raise ValueError(f"edge references unknown node: {a!r}")
        if b not in nodes:
            raise ValueError(f"edge references unknown node: {b!r}")
        if (b, a) not in edge_lookup:
            raise ValueError(f"asymmetric edge: {a!r} -> {b!r} but no reverse")

    for (a, b), _direction in directions.items():
        if a not in nodes:
            raise ValueError(f"direction references unknown node: {a!r}")
        if b not in nodes:
            raise ValueError(f"direction references unknown node: {b!r}")
        if (a, b) not in edge_lookup:
            # directions ⊆ edges 가 깨지면 데이터 누락 신호
            raise ValueError(
                f"direction {a!r} -> {b!r} has no matching edge"
            )


def dijkstra(graph: GraphData, start: str, goal: str) -> list[str]:
    """Shortest path (by hop count) from start to goal.

    Raises:
        InvalidNodeError: start or goal is not in the graph.
        NoRouteError: no path exists.
    """
    if not graph.has_node(start):
        raise InvalidNodeError(f"Unknown node id: {start!r}")
    if not graph.has_node(goal):
        raise InvalidNodeError(f"Unknown node id: {goal!r}")

    if start == goal:
        return [start]

    distances: dict[str, int] = {start: 0}
    came_from: dict[str, str] = {}
    heap: list[tuple[int, str]] = [(0, start)]

    while heap:
        cost, node = heapq.heappop(heap)
        if node == goal:
            break
        if cost > distances.get(node, 1 << 30):
            continue
        for neighbor in graph.neighbors(node):
            new_cost = cost + 1
            if new_cost < distances.get(neighbor, 1 << 30):
                distances[neighbor] = new_cost
                came_from[neighbor] = node
                heapq.heappush(heap, (new_cost, neighbor))

    if goal not in distances:
        raise NoRouteError(f"No route from {start!r} to {goal!r}")

    return _reconstruct_path(came_from, start, goal)


def _reconstruct_path(came_from: dict[str, str], start: str, goal: str) -> list[str]:
    path = [goal]
    while path[-1] != start:
        path.append(came_from[path[-1]])
    path.reverse()
    return path


def assert_connected(graph: GraphData, a: str, b: str) -> None:
    """Raise NotConnectedError if a and b are not directly adjacent."""
    if not graph.has_node(a):
        raise InvalidNodeError(f"Unknown node id: {a!r}")
    if not graph.has_node(b):
        raise InvalidNodeError(f"Unknown node id: {b!r}")
    if not graph.is_connected(a, b):
        raise NotConnectedError(f"Nodes {a!r} and {b!r} are not directly connected")
