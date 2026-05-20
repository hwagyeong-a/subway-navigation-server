\# 2026-05-20 — 방위각 데이터 통합 (DB v2: 5 테이블 + node\_directions)



\## 한 일



\- `node\_directions` 테이블 신규 추가 — 박경찬님 방위각 데이터 20개 적재 (절대 방위각 + cardinal + clock\_position)

\- `node\_edges` 수정 — `station\_exit ↔ fare\_gate` 직접 연결 제거 → `floor1\_hall` 경유로 변경 (박경찬님 새 설계 반영)

\- `scripts/subway\_nav\_full.sql` v2 갱신 — 4 테이블 → 5 테이블, 시드 데이터 INSERT 포함

\- `docs/db-setup.md` v2 갱신 — node\_directions 임포트 가이드 + 앱 측 사용법 추가

\- 양방향 일관성 검증 쿼리 작성 — 측정 오차 분포 확인 (직선 \~7°, 계단/분기점 30\~45°)

\- `/locate` API 재검증 — `{"node": "b1\_stairs"}` 정상 응답

\- GitHub fork (`hwagyeong-a/subway-navigation-server`) 에 force push 로 백업 완료



\## 왜 이렇게 했는지



\- \*\*node\_directions 를 별도 테이블로 분리\*\*: 박경찬님 설계 의도. `node\_edges` 는 그래프 구조(어디로 갈 수 있나)만, `node\_directions` 는 물리적 방향(어느 쪽으로 가나)만 담당. SRP(단일 책임 원칙) 준수.

\- \*\*양방향 방위각 그대로 저장\*\*: 180도 차이로 추정하지 않고 박경찬님이 직접 측정한 값 그대로 사용. 계단/분기점에서 양방향이 정확히 180도 안 됨 (측정에서 30\~45도 차이 발견). 현장 실측이 정답.

\- \*\*`station\_exit ↔ floor1\_hall` 경유 구조 채택\*\*: 박경찬님 새 측위 설계 그대로 반영. 노드 순서가 `1→2→3` 으로 자연스러워짐.

\- \*\*본인 KNN/wifi\_filter 코드 변경 0줄\*\*: node\_directions 는 방향 API 영역이라 본인 KNN과 무관. 데이터/스키마만 추가하고 코드는 그대로.



\## 막힌 것 / 결정 미뤄진 것



\- \*\*`/direction` API 가 DB 의 node\_directions 를 사용하지 않음\*\*: 현재 팀 A 의 `/direction` 은 `data/nodes.json` 좌표 기반으로 `atan2` 계산. 박경찬님의 실측 방위각을 활용하려면 팀 A 측 API 수정 필요. 5/15 미팅 안건.

\- \*\*`/collect` API (앱 → DB 자동 적재)\*\*: 시연 후 작업. 분담: 저=db/raw\_repository.py, A님=api/collect.py.

\- \*\*`data/{nodes,edges,danger}.json` 갱신\*\*: 팀 A 영역. 새 노드 ID (`station\_exit` 등 11개) 로 갱신 필요.



\## 다음에 할 일

\- 본인 fork → 팀 원본 PR 생성 + 팀 A 머지 요청

\- 단톡방 공유 (박경찬님께 방위각 적재 완료 보고, 예진님께 PR 알림)

\-  `/direction` API 가 DB node\_directions 를 활용하도록 변경 제안



\## 관련 커밋



\- `b9e6a13` feat(db): node\_directions 테이블 추가 (박경찬님 방위각 데이터)

\- `ca467cf` docs(worklog): 2026-05-15 팀 B 실측 데이터 도입 기록

\- `18ae692` feat(team-b): DB 모듈 + KNN + wifi\_filter + init\_db 추가

