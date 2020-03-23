import logging
from typing import Optional, Sequence

from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.web import Application

from ..admin.runner import start_admin
from ..mock.callbacks import CallbackManager, callback_manager
from ..mock.response_matcher import ResponseMatcher
from ..mock.specs import OpenAPISpecification
from ..mock.views import MockServerView
from ..utils.routing import PathRouting, Routing
from .log import FileSink, Log, NoSink
from .scope import Scope

logger = logging.getLogger(__name__)


def make_mocking_app_(
    callback_manager: CallbackManager,
    response_matcher: ResponseMatcher,
    router: Routing,
    log: Log,
):
    dependencies = dict(
        callback=callback_manager,
        response_matcher=response_matcher,
        router=router,
        log=log,
    )
    return Application([(r"/.*", MockServerView, dependencies)])


def make_mocking_app(
    callback_dir: Optional[str],
    specs: Sequence[OpenAPISpecification],
    routing: Routing,
    log: Log,
):
    # callback_manager = CallbackManager()
    if callback_dir is not None:
        callback_manager.load(callback_dir)

    response_matcher = ResponseMatcher(specs)

    return make_mocking_app_(callback_manager, response_matcher, routing, log)


class MockServer:
    def __init__(
        self,
        port,
        specs,
        scope: Optional[Scope] = None,
        callback_dir=None,
        admin_port=None,
        routing=PathRouting(),
        log_dir: Optional[str] = None,
    ):
        self._callback_dir = callback_dir
        self._admin_port = admin_port
        self._port = port
        self._specs = specs
        self._routing = routing
        self._scope = scope or Scope()
        self._log = Log(self._scope, NoSink() if log_dir is None else FileSink(log_dir))

    def run(self) -> None:
        if self._admin_port:
            start_admin(port=self._admin_port, scope=self._scope)
        app = make_mocking_app(
            self._callback_dir, self._specs, self._routing, self._log
        )
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

        logger.info("✓ Meeshkan is running")
