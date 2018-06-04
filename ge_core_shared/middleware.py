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

        # Some paths do not need an authorized user.
        if request.path in UNPROTECTED_API_ENDPOINTS:
            return self.app(environ, start_response)

        # Check if key is present and known.
        key = request.headers.get(API_KEY_HEADER, None)
        if key and key in ALLOWED_API_KEYS:
            return self.app(environ, start_response)

        # Deny the API call.
        response = Response("Unauthorized", status="401")
        return response(environ, start_response)
