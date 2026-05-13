"""Team B: PyMySQL connection lifecycle.

Per-request connection cached on `flask.g`, closed automatically on
teardown. Uses app.config DB_* values (set by Team A in config.py).
"""
from typing import Any

import pymysql
from flask import current_app, g


def get_connection() -> Any:
    """Return a PyMySQL connection scoped to the current request.

    Must be called inside a Flask application/request context.
    The connection is created lazily on first call and reused for
    the remainder of the context.
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
        # cursorclass 기본값(Cursor) 사용 → fetchall()이 tuple of tuples 반환.
        # fingerprint.py 가 인덱스 접근(r[0], r[1], r[2])을 가정하므로 변경 금지.
    )
    return g.db_conn


def close_connection(_exc: BaseException | None = None) -> None:
    """Teardown hook: close the per-request connection if it exists."""
    conn = g.pop("db_conn", None)
    if conn is not None:
        try:
            conn.close()
        except Exception:
            # teardown 중 예외는 삼킨다 (요청 응답에 영향 주면 안 됨)
            pass


def init_db(app) -> None:
    """Register teardown hook. Call from create_app()."""
    app.teardown_appcontext(close_connection)
