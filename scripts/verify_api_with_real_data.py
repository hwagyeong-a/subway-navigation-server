#!/usr/bin/env python3
"""박경찬 실측 데이터로 3개 API 의 응답을 자동 검증.

- /locate   : raw_measurements 의 각 스캔(노드별 10회)을 질의로 보내,
              KNN 이 측정한 노드를 맞히는지 정확도(accuracy) 측정 + 혼동표
- /route    : 모든 (출발, 목적지) 노드 쌍에 대해 경로가 반환되는지 (연결성)
- /direction: node_directions 의 모든 인접 엣지에 대해 방위각이 반환되는지

사용:
    python scripts/verify_api_with_real_data.py
    python scripts/verify_api_with_real_data.py --base-url https://xxx.ngrok-free.dev
"""
import argparse
import collections
import os

import pymysql
import requests
from dotenv import load_dotenv

load_dotenv()

HEADERS = {
    "Content-Type": "application/json",
    "ngrok-skip-browser-warning": "true",
}


def db_conn():
    return pymysql.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=int(os.getenv("DB_PORT", "6306")),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", "lowell"),
        database=os.getenv("DB_NAME", "subway_nav"),
        charset="utf8mb4",
    )


def load_scans(conn):
    """raw_measurements 를 (location, sample_id) 단위 스캔으로 묶는다."""
    scans: dict[tuple[str, int], list[tuple[str, int]]] = collections.defaultdict(list)
    with conn.cursor() as cur:
        cur.execute(
            "SELECT location, sample_id, mac, rssi_dBm FROM raw_measurements"
        )
        for location, sample_id, mac, rssi in cur.fetchall():
            scans[(location, sample_id)].append((mac, int(rssi)))
    return scans


def load_nodes(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT location FROM nodes ORDER BY node_order")
        return [r[0] for r in cur.fetchall()]


def load_edges(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT from_node, to_node FROM node_directions")
        return cur.fetchall()


def verify_locate(base_url, scans):
    print("\n" + "=" * 60)
    print("  /locate 정확도 검증 (raw 스캔 → KNN)")
    print("=" * 60)
    total = correct = 0
    per_node = collections.defaultdict(lambda: [0, 0])  # node -> [correct, total]
    confusion = collections.Counter()  # (actual, predicted) -> count

    for (actual, _sample), readings in sorted(scans.items()):
        wifi = [{"bssid": mac, "rssi": rssi} for mac, rssi in readings]
        r = requests.post(
            f"{base_url}/locate", json={"wifi": wifi}, headers=HEADERS, timeout=10
        )
        if r.status_code != 200:
            print(f"  [ERROR] {actual} sample → HTTP {r.status_code}: {r.text[:80]}")
            continue
        predicted = r.json().get("node")
        total += 1
        per_node[actual][1] += 1
        if predicted == actual:
            correct += 1
            per_node[actual][0] += 1
        else:
            confusion[(actual, predicted)] += 1

    print(f"\n  전체 정확도: {correct}/{total} = {correct / total * 100:.1f}%\n")
    print(f"  {'노드':<24} {'정답/시도':>10} {'정확도':>8}")
    print("  " + "-" * 44)
    for node, (c, t) in per_node.items():
        acc = c / t * 100 if t else 0
        mark = "✅" if acc == 100 else ("⚠️" if acc >= 60 else "❌")
        print(f"  {node:<24} {f'{c}/{t}':>10} {acc:>6.0f}% {mark}")

    if confusion:
        print("\n  오분류 (실제 → 예측):")
        for (a, p), n in confusion.most_common():
            print(f"    {a}  →  {p}   ({n}회)")
    return correct, total


def verify_route(base_url, nodes):
    print("\n" + "=" * 60)
    print("  /route 연결성 검증 (모든 노드 쌍)")
    print("=" * 60)
    ok = fail = 0
    failures = []
    for a in nodes:
        for b in nodes:
            if a == b:
                continue
            r = requests.post(
                f"{base_url}/route", json={"from": a, "to": b},
                headers=HEADERS, timeout=10,
            )
            if r.status_code == 200 and r.json().get("path"):
                ok += 1
            else:
                fail += 1
                code = (r.json().get("error", {}) or {}).get("code", r.status_code)
                failures.append((a, b, code))
    print(f"\n  도달 가능: {ok}/{ok + fail} 쌍")
    if failures:
        print("  실패 쌍:")
        for a, b, code in failures[:20]:
            print(f"    {a} → {b}  [{code}]")
    return ok, ok + fail


def verify_direction(base_url, edges):
    print("\n" + "=" * 60)
    print("  /direction 검증 (모든 인접 엣지)")
    print("=" * 60)
    ok = fail = 0
    failures = []
    for a, b in edges:
        r = requests.post(
            f"{base_url}/direction", json={"from": a, "to": b},
            headers=HEADERS, timeout=10,
        )
        if r.status_code == 200 and "angle" in r.json():
            ok += 1
        else:
            fail += 1
            failures.append((a, b, r.status_code, r.text[:60]))
    print(f"\n  방위각 응답: {ok}/{ok + fail} 엣지")
    if failures:
        print("  실패 엣지:")
        for a, b, sc, msg in failures:
            print(f"    {a} → {b}  [{sc}] {msg}")
    return ok, ok + fail


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="http://127.0.0.1:5001")
    args = ap.parse_args()

    conn = db_conn()
    try:
        scans = load_scans(conn)
        nodes = load_nodes(conn)
        edges = load_edges(conn)
    finally:
        conn.close()

    print(f"대상 서버: {args.base_url}")
    print(f"스캔 {len(scans)}개 / 노드 {len(nodes)}개 / 엣지 {len(edges)}개")

    verify_locate(args.base_url, scans)
    verify_route(args.base_url, nodes)
    verify_direction(args.base_url, edges)
    print("\n검증 완료.\n")


if __name__ == "__main__":
    main()
