import logging

from tornado.httpserver import HTTPServer
from tornado.web import Application

from meeshkan.serve.admin.views import (
    RestMiddlewaresView,
    RestMiddlewareView,
    StorageView,
)
from meeshkan.serve.mock.rest import rest_middleware_manager
from meeshkan.serve.mock.storage import storage_manager

logger = logging.getLogger(__name__)


def make_admin_app(
    storage_manager=storage_manager, rest_middleware_manager=rest_middleware_manager
):
    storage_view_deps = dict(storage_manager=storage_manager)
    rest_middleware_deps = dict(rest_middleware_manager=rest_middleware_manager)
    return Application(
        [
            (r"/admin/storage", StorageView, storage_view_deps),
            (
                r"/admin/middleware/rest/pregen",
                RestMiddlewaresView,
                rest_middleware_deps,
            ),
            (
                r"/admin/middleware/rest/pregen/(.+)",
                RestMiddlewareView,
                rest_middleware_deps,
            ),
        ]
    )


def start_admin(port):
    app = make_admin_app()
    http_server = HTTPServer(app)
    http_server.listen(port)
    logger.info("• Admin   http://localhost:%s/admin", port)
