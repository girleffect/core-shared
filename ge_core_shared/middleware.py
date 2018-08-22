import time

from flask import request as flask_request

from werkzeug.wrappers import Request, Response

from prometheus_client import Histogram

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


class MetricMiddleware(object):

    def __init__(self, app, prefix):
        self.app = app
        self.H = Histogram(f"{prefix}_http_duration_seconds", "API duration",
              ["path_prefix", "method", "status"])
        self.app.before_request(self.start_timer)
        self.app.after_request(self.stop_timer)

    # def __call__(self, environ, start_response):
    #     request = Request(environ)
    #     start_time = time.time()
    #     response = self.app(environ, start_response)
    #     self.H.labels(
    #         path_prefix=request.path.split("/")[1],
    #         method=request.method,
    #         status=response.status).observe(time.time()-start_time)
    #     return response

    @staticmethod
    def start_timer():
        flask_request.start_time = time.time()

    def stop_timer(self, response):
        resp_time = time.time() - flask_request.start_time
        self.H.labels(
            path_prefix=flask_request.path.split("/")[1],
            method=flask_request.method,
            status=response.status).observe(resp_time)
        return response
