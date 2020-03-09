import logging

from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.web import Application

from meeshkan.server.admin.runner import start_admin
from meeshkan.server.server.callbacks import callback_manager
from meeshkan.server.server.response_matcher import ResponseMatcher
from meeshkan.server.server.views import MockServerView
from meeshkan.server.utils.routing import Routing, PathRouting

logger = logging.getLogger(__name__)


class MeeshkanApplication(Application):
    response_matcher: ResponseMatcher
    router: Routing


def make_mocking_app(callback_path, specs_dir, routing):
    app = MeeshkanApplication([
        (r'/.*', MockServerView)
    ])
    callback_manager.load(callback_path)

    app.response_matcher = ResponseMatcher(specs_dir)
    app.router = routing
    return app


class MockServer:
    def __init__(self, port, specs_dir, callback_path=None, admin_port=None, routing=PathRouting()):
        self._callback_path = callback_path
        self._admin_port = admin_port
        self._port = port
        self._specs_dir = specs_dir
        self._routing = routing

    def run(self):
        if self._admin_port:
            start_admin(self._admin_port)
        app = make_mocking_app(self._callback_path, self._specs_dir, self._routing)
        http_server = HTTPServer(app)
        http_server.listen(self._port)
        logger.info('Mock server is listening on http://localhost:%s', self._port)
        IOLoop.current().start()
