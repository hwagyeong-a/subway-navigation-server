from flask import jsonify, request

from ..core.locator import WifiSample, estimate
from . import bp
from .errors import EmptyWifiError, InvalidPayloadError, KnnError


@bp.route("/locate", methods=["POST"])
def locate():
    """현 위치 확인 (Wi-Fi Fingerprinting + KNN)
    ---
    tags:
      - locate
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
          required: [wifi]
          properties:
            wifi:
              type: array
              description: 측정된 Wi-Fi AP 목록
              items:
                type: object
                required: [bssid, rssi]
                properties:
                  bssid: { type: string, example: "aa:bb:cc:dd:ee:ff", description: AP MAC 주소 }
                  rssi:  { type: number, example: -65, description: "신호 세기 (dBm). int·float 모두 허용 (평균값 float 가능)" }
                  ssid:  { type: string, example: "Korail_WiFi_Free", description: "AP 이름 (선택). 보내면 서버측 이동성 기기 필터가 활성화됨" }
          example:
            wifi:
              - { bssid: "aa:bb:cc:dd:ee:ff", rssi: -65, ssid: "Korail_WiFi_Free" }
              - { bssid: "11:22:33:44:55:66", rssi: -72, ssid: "Public WiFi Free" }
              - { bssid: "77:88:99:aa:bb:cc", rssi: -88, ssid: "U+zone" }
    responses:
      200:
        description: 추정된 노드 ID
        schema:
          type: object
          properties:
            node: { type: string, example: "down_platform" }
      400:
        description: INVALID_PAYLOAD / EMPTY_WIFI
        schema:
          type: object
          properties:
            error:
              type: object
              properties:
                code:    { type: string, example: "EMPTY_WIFI" }
                message: { type: string, example: "'wifi' must not be empty" }
      500:
        description: KNN_ERROR — 추정 모듈 미등록 또는 내부 오류
        schema:
          type: object
          properties:
            error:
              type: object
              properties:
                code:    { type: string, example: "KNN_ERROR" }
                message: { type: string, example: "No estimator registered. ..." }
    """
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        raise InvalidPayloadError("Body must be a JSON object")

    wifi = payload.get("wifi")
    if not isinstance(wifi, list):
        raise InvalidPayloadError("'wifi' must be a list")
    if len(wifi) == 0:
        raise EmptyWifiError("'wifi' must not be empty")

    samples: list[WifiSample] = []
    for item in wifi:
        if not isinstance(item, dict):
            raise InvalidPayloadError("Each wifi item must be an object")
        bssid = item.get("bssid")
        rssi = item.get("rssi")
        # rssi 는 int 또는 float 허용 (앱이 최근 N개 평균을 보내면 float).
        # bool 은 isinstance(True, int) 가 True 라 명시적으로 배제.
        if (
            not isinstance(bssid, str)
            or isinstance(rssi, bool)
            or not isinstance(rssi, (int, float))
        ):
            raise InvalidPayloadError(
                "Each wifi item requires string bssid and numeric rssi"
            )
        # ssid 는 선택. 있으면 서버측 이동성 기기 필터(wifi_filter)가 활용.
        ssid = item.get("ssid")
        if ssid is not None and not isinstance(ssid, str):
            raise InvalidPayloadError("'ssid' must be a string if provided")
        samples.append(WifiSample(bssid=bssid, rssi=float(rssi), ssid=ssid))

    try:
        node_id = estimate(samples)
    except NotImplementedError as e:
        raise KnnError(str(e)) from e
    except Exception as e:
        raise KnnError(f"Estimator failed: {e}") from e

    return jsonify(node=node_id)
