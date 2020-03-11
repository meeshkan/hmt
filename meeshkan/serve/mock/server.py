import logging

from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.web import Application

from meeshkan.serve.admin.runner import start_admin
from meeshkan.serve.mock.callbacks import callback_manager
from meeshkan.serve.mock.response_matcher import ResponseMatcher
from meeshkan.serve.mock.views import MockServerView
from meeshkan.serve.utils.routing import Routing, PathRouting

logger = logging.getLogger(__name__)


class MeeshkanApplication(Application):
    response_matcher: ResponseMatcher
    router: Routing


def make_mocking_app(callback_dir, specs_dir, routing):
    app = MeeshkanApplication([(r"/.*", MockServerView)])
    if callback_dir:
        callback_manager.load(callback_dir)

    app.response_matcher = ResponseMatcher(specs_dir)
    app.router = routing
    return app


class MockServer:
    def __init__(
        self, port, specs_dir, callback_dir=None, admin_port=None, routing=PathRouting()
    ):
        self._callback_dir = callback_dir
        self._admin_port = admin_port
        self._port = port
        self._specs_dir = specs_dir
        self._routing = routing

    def run(self):
        if self._admin_port:
            start_admin(self._admin_port)
        app = make_mocking_app(self._callback_dir, self._specs_dir, self._routing)
        http_server = HTTPServer(app)
        http_server.listen(self._port)
        logger.info("Mock mock is listening on http://localhost:%s", self._port)
        IOLoop.current().start()
