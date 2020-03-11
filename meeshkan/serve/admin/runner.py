import logging

from tornado.httpserver import HTTPServer
from tornado.web import Application

from meeshkan.serve.admin.views import (
    StorageView,
    RestMiddlewaresView,
    RestMiddlewareView,
)

logger = logging.getLogger(__name__)


def make_admin_app():
    return Application(
        [
            (r"/admin/storage", StorageView),
            (r"/admin/middleware/rest/pregen", RestMiddlewaresView),
            (r"/admin/middleware/rest/pregen/(.+)", RestMiddlewareView),
        ]
    )


def start_admin(port):
    app = make_admin_app()
    http_server = HTTPServer(app)
    http_server.listen(port)
    logger.info("Starting admin endpont on http://localhost:%s/admin", port)
