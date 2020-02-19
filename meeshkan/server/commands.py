import logging
import os

import click
import tornado.ioloop
import yaml
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.web import Application

from .utils.routing import PathRouting, HeaderRouting, Routing
from .admin.views import RestMiddlewareView, RestMiddlewaresView, StorageView
from .proxy.proxy import RecordProxy
from .server.callbacks import callback_manager
from .server.response_matcher import ResponseMatcher
from .server.views import MockServerView
from .utils.data_callback import RequestLoggingCallback

LOG_CONFIG = os.path.join(os.path.dirname(__file__), 'logging.yaml')
logger = logging.getLogger(__name__)

def make_admin_app():
    return Application([
        (r'/admin/storage', StorageView),
        (r'/admin/rest_middleware', RestMiddlewaresView),
        (r'/admin/rest_middleware/(.+)', RestMiddlewareView),
    ])

def start_admin(port):
    app = make_admin_app()
    http_server = HTTPServer(app)
    http_server.listen(port)
    logger.info('Starting admin endpont on http://localhost:%s/admin', port)



@click.command()
@click.option('--port', default="8000", help='Server port')
@click.option('--admin_port', default="8888", help='Admin server port')
@click.option('--log_dir', default="./logs", help='API calls logs direcotry')
@click.option('--header_routing', is_flag=True, help='Whether to use a header based routing to a target host')
@click.option('--schema_dir', default="./__unmock__", help='Directory with OpenAPI schemas')
def record(port, admin_port, log_dir, header_routing, schema_dir):
    """
    Record http traffic to http-types format.
    """
    start_admin(admin_port)
    logger.info('Starting Meeshkan proxy in recording mode on http://localhost:%s', port)
    with RequestLoggingCallback(recording=True, log_dir=log_dir, schema_dir=schema_dir) as callback:
        server = RecordProxy(callback, HeaderRouting() if header_routing else PathRouting())
        server.listen(port)
        tornado.ioloop.IOLoop.instance().start()

class MeeshkanApplication(Application):
    response_matcher: ResponseMatcher
    router: Routing

def make_mocking_app(callback_path, schema_dir, router):
    app = MeeshkanApplication([
        (r'/.*', MockServerView)
    ])
    callback_manager.load(callback_path)

    app.response_matcher = ResponseMatcher(schema_dir)
    app.router = router
    return app

@click.command()
@click.option('--callback_path', default="./callbacks", help='Directory with configured callbacks')
@click.option('--admin_port', default="8888", help='Admin server port')
@click.option('--port', default="8000", help='Server port')
@click.option('-s', '--schema_dir', default="./__unmock__", help='Directory with OpenAPI schemas')
@click.option('--header_routing', is_flag=True, help='Whether to use a path based routing to a target host')
def mock(callback_path, admin_port, port, schema_dir, header_routing):
    start_admin(admin_port)
    app = make_mocking_app(callback_path, schema_dir, HeaderRouting() if header_routing else PathRouting())
    http_server = HTTPServer(app)
    http_server.listen(port)
    logger.info('Mock server is listening on http://localhost:%s', port)
    IOLoop.current().start()
