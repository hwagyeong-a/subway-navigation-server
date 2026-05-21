from flask import Flask, jsonify


class AppError(Exception):
    """Base for all domain errors that map to API error responses.

    See docs/05-API명세.md §5.5 for the error envelope format.
    """

    code: str = "INTERNAL_ERROR"
    http_status: int = 500

    def __init__(self, message: str = ""):
        super().__init__(message)
        self.message = message or self.code


class InvalidPayloadError(AppError):
    code = "INVALID_PAYLOAD"
    http_status = 400


class EmptyWifiError(AppError):
    code = "EMPTY_WIFI"
    http_status = 400


class InvalidNodeError(AppError):
    code = "INVALID_NODE"
    http_status = 400


class NotConnectedError(AppError):
    code = "NOT_CONNECTED"
    http_status = 400


class NoRouteError(AppError):
    code = "NO_ROUTE"
    http_status = 404


class KnnError(AppError):
    code = "KNN_ERROR"
    http_status = 500


class DbError(AppError):
    code = "DB_ERROR"
    http_status = 500


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(AppError)
    def _handle_app_error(err: AppError):
        return (
            jsonify(error={"code": err.code, "message": err.message}),
            err.http_status,
        )

    @app.errorhandler(404)
    def _handle_not_found(_):
        return (
            jsonify(error={"code": "NOT_FOUND", "message": "Not found"}),
            404,
        )

    @app.errorhandler(405)
    def _handle_method_not_allowed(_):
        return (
            jsonify(error={"code": "METHOD_NOT_ALLOWED", "message": "Method not allowed"}),
            405,
        )
