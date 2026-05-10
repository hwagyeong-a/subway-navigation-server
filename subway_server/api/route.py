from flask import current_app, jsonify, request

from ..core.graph import GraphData, dijkstra
from . import bp
from .errors import InvalidPayloadError


@bp.route("/route", methods=["POST"])
def route():
    """경로 탐색 (위험 노드 자동 회피)
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
              example: "A"
              description: 출발 노드 ID
            to:
              type: string
              example: "F"
              description: 목적지 노드 ID (위험 노드 지정 시 400)
          example:
            from: "A"
            to: "F"
    responses:
      200:
        description: 경로 (출발지 → 목적지 노드 ID 순서 배열)
        schema:
          type: object
          properties:
            path:
              type: array
              items: { type: string }
              example: ["A", "B", "C", "D", "F"]
      400:
        description: INVALID_NODE / DANGER_DESTINATION / INVALID_PAYLOAD
        schema:
          type: object
          properties:
            error:
              type: object
              properties:
                code:    { type: string, example: "DANGER_DESTINATION" }
                message: { type: string, example: "Destination is a danger node: 'E'" }
      404:
        description: NO_ROUTE — 위험 노드 제외 시 도달 불가
        schema:
          type: object
          properties:
            error:
              type: object
              properties:
                code:    { type: string, example: "NO_ROUTE" }
                message: { type: string, example: "No safe route from 'A' to 'Z'" }
    """
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        raise InvalidPayloadError("Body must be a JSON object")
    a = payload.get("from")
    b = payload.get("to")
    if not isinstance(a, str) or not isinstance(b, str):
        raise InvalidPayloadError("'from' and 'to' must be strings")

    graph: GraphData = current_app.config["GRAPH"]
    path = dijkstra(graph, a, b)
    return jsonify(path=path)
