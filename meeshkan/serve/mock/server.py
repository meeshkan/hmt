import logging
from typing import Optional, Sequence

from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.web import Application

from meeshkan.serve.admin.runner import start_admin
from meeshkan.serve.mock.callbacks import CallbackManager, callback_manager
from meeshkan.serve.mock.response_matcher import ResponseMatcher
from meeshkan.serve.mock.specs import OpenAPISpecification
from meeshkan.serve.mock.views import MockServerView
from meeshkan.serve.utils.routing import PathRouting, Routing

logger = logging.getLogger(__name__)


def make_mocking_app_(
    callback_manager: CallbackManager,
    response_matcher: ResponseMatcher,
    router: Routing,
):
    dependencies = dict(
        callback=callback_manager, response_matcher=response_matcher, router=router,
    )
    return Application([(r"/.*", MockServerView, dependencies)])


def make_mocking_app(
    callback_dir: Optional[str], specs: Sequence[OpenAPISpecification], routing: Routing
):
    # callback_manager = CallbackManager()
    if callback_dir is not None:
        callback_manager.load(callback_dir)

    response_matcher = ResponseMatcher(specs)

    return make_mocking_app_(callback_manager, response_matcher, routing)


class MockServer:
    def __init__(
        self, port, specs, callback_dir=None, admin_port=None, routing=PathRouting()
    ):
        self._callback_dir = callback_dir
        self._admin_port = admin_port
        self._port = port
        self._specs = specs
        self._routing = routing

    def run(self) -> None:
        if self._admin_port:
            start_admin(self._admin_port)
        app = make_mocking_app(self._callback_dir, self._specs, self._routing)
        http_server = HTTPServer(app)
        http_server.listen(self._port)
        self.log_startup()
        IOLoop.current().start()

    def log_startup(self) -> None:
        for spec in self._specs:
            if not spec.api.servers:
                continue
            for path, path_item in spec.api.paths.items():
                for method in [
                    "get",
                    "put",
                    "post",
                    "delete",
                    "options",
                    "head",
                    "patch",
                    "trace",
                ]:
                    if getattr(path_item, method):
                        logger.info(
                            "→ "
                            + method.upper().ljust(7)
                            + f" http://localhost:{self._port}/"
                            + spec.api.servers[0].url
                            + path
                        )
