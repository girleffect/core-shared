from werkzeug.wrappers import Request, Response

from project.settings import ALLOWED_API_KEYS, API_KEY_HEADER


class AuthMiddleware(object):

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        request = Request(environ)
        key = request.headers.get(API_KEY_HEADER, None)
        if key and key in ALLOWED_API_KEYS:
            return self.app(environ, start_response)
        response = Response("Unauthorized", status="401")
        return response(environ, start_response)
