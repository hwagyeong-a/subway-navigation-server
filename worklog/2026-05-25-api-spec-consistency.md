# 2026-05-25 (2) — API 명세 ↔ 구현 정합성 점검 + 수정

## 한 일
- `docs/05-API명세.md` ↔ 실제 구현(`subway_server/api/`) 전수 대조
- 발견된 불일치 5건 처리:

| # | 항목 | 심각도 | 처리 |
|---|---|---|---|
| 1 | `/locate` rssi int-only → 앱 평균값(float) 거부 | 🔴 통합 깨짐 | int·float 모두 허용 (`2999b0c`) |
| 2 | SSID 필터가 입력에 ssid 없어 잠자던 상태 | 🟡 | WifiSample/locate 에 ssid 추가 → 서버측 필터 활성화 (`6986ddd`) |
| 3 | `/locate` 예시가 옛 노드 `"B"` | 🟢 문서 | `down_platform` 으로 정정 |
| 4 | `/locate` 시퀀스 다이어그램 책임 주체 오류 | 🟢 문서 | 정렬·필터·KNN 은 KNN 모듈임을 명시 |
| 5 | 에러 표에 404/405 누락 | 🟢 문서 | NOT_FOUND, METHOD_NOT_ALLOWED 추가 |

- 테스트 59 → **66** (float 허용 1, bool 거부 1, wifi_filter 5 신규)
- 라이브 서버(ngrok) 재시작하여 모든 수정 반영·검증

## 왜 이렇게 했는지
- **rssi float (1번)**: 박경찬 앱 컨셉이 "최근 3개 평균" → 평균값은 float. 기존 int-only 검증이면 통합 즉시 INVALID_PAYLOAD 로 깨졌을 것. 통합 테스트 전에 선제 수정.
- **SSID 필터 (2번)**: 화경 `wifi_filter.py` 가 이미 `getattr(s, "ssid", None)` 로 ssid 대기 중이었음(그분 주석에 "추가되면 즉시 동작"). WifiSample 에 필드만 더하니 코드 변경 없이 활성화 — 앱 1차 + 서버 2차 이중 필터.
- **문서 3건 (3·4·5)**: 동작엔 문제 없지만 교수님·팀원이 문서 보고 오해할 소지. 발표 자료로 docs 를 쓸 거라 정확도 유지.

## 막힌 것 / 결정 미뤄진 것
- **ssid 는 선택 필드**로 둠 — 앱이 안 보내도 동작(RSSI 필터만), 보내면 SSID 필터까지. 최수빈 앱이 ssid 동봉할지는 통합 시 협의.
- SSID 필터는 KNN 모듈(`knn_estimate`) 내부에서 실행되므로 **실 KNN 경로에서만** 작동 (stub/fake_estimator 테스트에선 미실행). 단위 테스트는 `filter_wifi_samples` 직접 호출로 검증.

## 다음에 할 일
- 최수빈에게 변경점 2건 공유 (rssi float 허용 / ssid 선택 동봉 권장)
- 앱 ↔ 서버 통합 테스트 시 `/route` 응답 형식(객체 배열) 호환성 확인

## 관련 커밋
- `2999b0c` fix(locate): accept float rssi (앱 평균값 대응)
- `6986ddd` feat(locate): server-side SSID filter + doc fixes (#2~#5)
