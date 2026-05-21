from flask import current_app, jsonify, request

from ..core.graph import GraphData
from . import bp
from .errors import InvalidNodeError, InvalidPayloadError, NotConnectedError


@bp.route("/direction", methods=["POST"])
def direction():
    """노드 간 절대 방위각 반환 (박경찬 실측 데이터)
    ---
    tags:
      - direction
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
              description: 현재 노드 ID (location)
            to:
              type: string
              example: "floor1_hall"
              description: 다음 노드 ID (직접 연결되어 있어야 함)
          example:
            from: "station_exit"
            to: "floor1_hall"
    responses:
      200:
        description: 절대 방위각 + 8방위 + 시계 방향
        schema:
          type: object
          properties:
            angle:
              type: number
              example: 268
              description: 절대 방위각 (0~360°, 정북=0, 시계방향)
            cardinal:
              type: string
              example: "W"
              description: 8방위 (N/NE/E/SE/S/SW/W/NW)
            clock:
              type: integer
              example: 9
              description: 시계 방향 (1~12시)
      400:
        description: INVALID_NODE / NOT_CONNECTED / INVALID_PAYLOAD
        schema:
          type: object
          properties:
            error:
              type: object
              properties:
                code:    { type: string, example: "NOT_CONNECTED" }
                message: { type: string, example: "Nodes 'station_exit' and 'b1_stairs' are not directly connected" }
    """
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        raise InvalidPayloadError("Body must be a JSON object")
    a = payload.get("from")
    b = payload.get("to")
    if not isinstance(a, str) or not isinstance(b, str):
        raise InvalidPayloadError("'from' and 'to' must be strings")

    graph: GraphData = current_app.config["GRAPH"]
    if not graph.has_node(a):
        raise InvalidNodeError(f"Unknown node id: {a!r}")
    if not graph.has_node(b):
        raise InvalidNodeError(f"Unknown node id: {b!r}")

    d = graph.direction(a, b)
    if d is None:
        raise NotConnectedError(
            f"No direction data for {a!r} -> {b!r} (nodes not directly connected)"
        )

    return jsonify(
        angle=d.heading_degrees,
        cardinal=d.cardinal,
        clock=d.clock_position,
    )
