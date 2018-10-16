import time

from flask import request as flask_request
from prometheus_client import Histogram
from werkzeug.wrappers import Request, Response

from project.settings import ALLOWED_API_KEYS, API_KEY_HEADER

try:
    from project.settings import UNPROTECTED_API_ENDPOINTS
except ImportError:
    UNPROTECTED_API_ENDPOINTS = set()

# NOTE: If a flask middleware function returns None, normal processing of the
# request will continue. Anything else will immediately return that as a
# response.
def auth_middleware(app, service_name):

    def before_request():
        request = flask_request

        # Some paths do not need an authorization key.
        if request.path not in UNPROTECTED_API_ENDPOINTS:
            # Check if key is present and known.
            key = request.headers.get(API_KEY_HEADER, None)
            if not key or key not in ALLOWED_API_KEYS:
                # Deny the API call.
                return Response("Unauthorized", status="401")

    app.before_request(before_request)


def metric_middleware(app, service_name):
    """
    Middleware to add Prometheus metrics for request durations.
    :param app: The flask app to which to add the middleware.
    :param service_name: The name of the service the metrics fall under.
    """
    denial_replacers = {
        404: "not_found",
        401: "unauthorized"
    }
    H = Histogram(f"{service_name}_http_duration_seconds", "API duration",
          ["path_prefix", "method", "status"])

    def start_timer():
        flask_request.start_time = time.time()

    def stop_timer(response):
        resp_time = time.time() - flask_request.start_time
        path = flask_request.path.replace("/api/v1", "")
        path_prefix = self.denial_replacers.get(
            response.status, path.split("/")[1]
        )
        H.labels(
            path_prefix=path_prefix,
            method=flask_request.method,
            status=response.status).observe(resp_time)
        return response

    app.before_request(start_timer)
    app.after_request(stop_timer)
