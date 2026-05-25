from flask import Flask
from flasgger import Swagger
from config import Config
from .api import register_blueprints
from .api.errors import register_error_handlers
from .core.graph import load_graph


def create_app(config_obj: type = Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_obj)
    app.config["GRAPH"] = load_graph(app.config["DATA_DIR"])

    # Swagger UI "Try it out" 요청에 ngrok 경고 우회 헤더를 자동 주입.
    # (ngrok 무료 도메인은 헤더 없으면 경고 HTML 을 반환함. ngrok 아닌
    #  환경에선 이 헤더가 무시되므로 항상 켜둬도 무해.)
    swagger_config = dict(Swagger.DEFAULT_CONFIG)
    swagger_config["ui_params_text"] = (
        '{ "requestInterceptor": (req) => { '
        'req.headers["ngrok-skip-browser-warning"] = "true"; return req; } }'
    )

    Swagger(
        app,
        config=swagger_config,
        template={
            "info": {
                "title": "지하철역 보행지원 서버 API",
                "description": (
                    "Team A (이예진) - Flask 백엔드. "
                    "docs/05-API명세.md 와 동기화됨."
                ),
                "version": "0.1.0",
            },
            "consumes": ["application/json"],
            "produces": ["application/json"],
        },
    )

    # Team B: DB connection 의 teardown 훅 등록
    from .db.connection import init_db
    init_db(app)

    register_error_handlers(app)
    register_blueprints(app)
    if not app.config.get("TESTING"):
        _try_register_real_estimator()
    return app


def _try_register_real_estimator() -> None:
    """Team B will provide subway_server/core/knn.py.
    Until then, the default stub raises NotImplementedError on /locate.
    """
    try:
        from .core.knn import knn_estimate  # type: ignore
        from .core.locator import register_estimator
        register_estimator(knn_estimate)
    except ImportError:
        pass