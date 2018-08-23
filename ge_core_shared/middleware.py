import time

from flask import request as flask_request
from prometheus_client import Histogram
from werkzeug.wrappers import Request, Response

from project.settings import ALLOWED_API_KEYS, API_KEY_HEADER

try:
    from project.settings import UNPROTECTED_API_ENDPOINTS
except ImportError:
    UNPROTECTED_API_ENDPOINTS = set()


class AuthMiddleware(object):

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        request = Request(environ)

        # Some paths do not need an authorization key.
        if request.path in UNPROTECTED_API_ENDPOINTS:
            return self.app(environ, start_response)

        # Check if key is present and known.
        key = request.headers.get(API_KEY_HEADER, None)
        if key and key in ALLOWED_API_KEYS:
            return self.app(environ, start_response)

        # Deny the API call.
        response = Response("Unauthorized", status="401")
        return response(environ, start_response)


def metric_middleware(app, service_name):
    """
    Middleware to add Prometheus metrics for request durations.
    :param app: The flask app to which to add the middleware.
    :param service_name: The name of the service the metrics fall under.
    """
    H = Histogram(f"{service_name}_http_duration_seconds", "API duration",
          ["path_prefix", "method", "status"])

    def start_timer():
        flask_request.start_time = time.time()

    def stop_timer(response):
        resp_time = time.time() - flask_request.start_time
        path = flask_request.path.replace("/api/v1", "")
        H.labels(
            path_prefix=path.split("/")[1],
            method=flask_request.method,
            status=response.status).observe(resp_time)
        return response

    app.before_request(start_timer)
    app.after_request(stop_timer)
