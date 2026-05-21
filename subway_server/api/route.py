from flask import current_app, jsonify, request

from ..core.graph import GraphData, dijkstra
from . import bp
from .errors import InvalidPayloadError


@bp.route("/route", methods=["POST"])
def route():
    """경로 탐색 (hop 수 최소, edge_type 포함)
    ---
    tags:
      - route
    consumes:
      - application/json
    produces:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [from, to]
          properties:
            from:
              type: string
              example: "station_exit"
              description: 출발 노드 ID
            to:
              type: string
              example: "down_platform"
              description: 목적지 노드 ID
          example:
            from: "station_exit"
            to: "down_platform"
    responses:
      200:
        description: 출발지 → 목적지 경로. 각 노드에 floor / zone / edge_to_next 포함
        schema:
          type: object
          properties:
            path:
              type: array
              items:
                type: object
                properties:
                  node:         { type: string, example: "station_exit" }
                  floor:        { type: string, example: "ground" }
                  zone:         { type: string, example: "entrance" }
                  edge_to_next: { type: string, example: "flat", description: "flat | stairs | branch | null(마지막 노드)" }
              example:
                - { node: "station_exit",   floor: "ground", zone: "entrance", edge_to_next: "flat" }
                - { node: "floor1_hall",    floor: "1F",     zone: "hall",     edge_to_next: "flat" }
                - { node: "fare_gate",      floor: "1F",     zone: "gate",     edge_to_next: "flat" }
                - { node: "floor1_stairs",  floor: "1F",     zone: "stairs",   edge_to_next: "stairs" }
                - { node: "stairs_mid",     floor: "mid",    zone: "stairs",   edge_to_next: "stairs" }
                - { node: "b1_stairs",      floor: "B1",     zone: "stairs",   edge_to_next: "flat" }
                - { node: "b1_elevator",    floor: "B1",     zone: "hall",     edge_to_next: "flat" }
                - { node: "b1_down_stairs_front", floor: "B1", zone: "branch", edge_to_next: "branch" }
                - { node: "down_platform",  floor: "B1",     zone: "platform", edge_to_next: null }
      400:
        description: INVALID_NODE / INVALID_PAYLOAD
      404:
        description: NO_ROUTE — 도달 불가
    """
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        raise InvalidPayloadError("Body must be a JSON object")
    a = payload.get("from")
    b = payload.get("to")
    if not isinstance(a, str) or not isinstance(b, str):
        raise InvalidPayloadError("'from' and 'to' must be strings")

    graph: GraphData = current_app.config["GRAPH"]
    path_nodes = dijkstra(graph, a, b)

    enriched: list[dict] = []
    for i, nid in enumerate(path_nodes):
        meta = graph.meta(nid)
        next_node = path_nodes[i + 1] if i + 1 < len(path_nodes) else None
        edge = graph.edge(nid, next_node) if next_node else None
        enriched.append({
            "node": nid,
            "floor": meta.floor,
            "zone": meta.zone,
            "edge_to_next": edge.edge_type if edge else None,
        })

    return jsonify(path=enriched)
