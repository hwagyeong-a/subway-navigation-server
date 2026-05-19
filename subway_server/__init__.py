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
    Swagger(
        app,
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
