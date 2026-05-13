"""Team B: MySQL PyMySQL 연결 모듈.

요청 단위로 connection을 flask.g 에 캐시하고,
요청 종료 시 teardown 훅이 자동으로 닫는다.
DB 자격증명은 app.config의 DB_* 값을 사용.
"""
from typing import Any

import pymysql
from flask import current_app, g


def get_connection() -> Any:
    """현재 Flask 요청에 묶인 PyMySQL connection을 반환.

    Flask 앱/요청 컨텍스트 안에서 호출해야 한다.
    첫 호출 시 connection이 생성되고, 같은 요청 내 재호출은
    캐시된 connection을 그대로 반환한다.
    """
    if "db_conn" in g:
        return g.db_conn

    cfg = current_app.config
    g.db_conn = pymysql.connect(
        host=cfg["DB_HOST"],
        user=cfg["DB_USER"],
        password=cfg["DB_PASSWORD"],
        database=cfg["DB_NAME"],
        port=cfg.get("DB_PORT", 3306),
        charset="utf8mb4",
        autocommit=True,
    )
    return g.db_conn


def close_connection(_exc: BaseException | None = None) -> None:
    """Teardown 훅: 요청 종료 시 connection을 닫는다."""
    conn = g.pop("db_conn", None)
    if conn is not None:
        try:
            conn.close()
        except Exception:
            pass


def init_db(app) -> None:
    """앱에 teardown 훅을 등록. create_app() 에서 호출되어야 함."""
    app.teardown_appcontext(close_connection)
