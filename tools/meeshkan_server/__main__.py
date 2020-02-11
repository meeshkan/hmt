import logging
import os

import click
import tornado.ioloop
import yaml
from tools.meeshkan_server.proxy.proxy import RecordProxy
from tools.meeshkan_server.server.mocking_service import MockingService
from tools.meeshkan_server.server.views import MockServerView
from tools.meeshkan_server.utils.data_callback import RequestLoggingCallback
from tornado.httpserver import HTTPServer
from tornado.web import Application
from tornado.ioloop import IOLoop

LOG_CONFIG = os.path.join(os.path.dirname(__file__), 'logging.yaml')
logger = logging.getLogger(__name__)

@click.group()
def main():
    if os.path.exists(LOG_CONFIG):
        with open(LOG_CONFIG) as f:
            config = yaml.safe_load(f)
            logging.config.dictConfig(config)
    else:
        logger.warning('No logging configuration provided in file %s. Using default configuratin.', LOG_CONFIG)




@main.command()
@click.option('--log_dir', default="./logs", help='Directory to store captured API calls records')
@click.option('--schema_dir', default="./__unmock__", help='Directory to store OpenAPI descriptions')
@click.option('--port', default="8000", help='Mocking server address')
def record(port, log_dir, schema_dir):
    logger.info('Starting Meeshkan proxy in recording mode')
    with RequestLoggingCallback(recording=True, log_dir=log_dir, schema_dir=schema_dir) as callback:
        server = RecordProxy(callback)
        server.listen(port)
        tornado.ioloop.IOLoop.instance().start()


@main.command()
@click.option('--callback_path', default="./callbacks/callback_sample.py", help='Mocking server address')
@click.option('--log_dir', default="./logs", help='Directory to store captured API calls records')
@click.option('--schema_dir', default="./__unmock__", help='Directory to store OpenAPI descriptions')
@click.option('--port', default="8000", help='Mocking server address')
def mock(port, log_dir, schema_dir, callback_path):
    app = Application([
        (r'/.*', MockServerView)
    ])
    app.mocking_service = MockingService(log_dir=log_dir, schema_dir=schema_dir, callback_path=callback_path)
    http_server = HTTPServer(app)
    http_server.listen(port)
    logger.info('Mock server is listening on http://localhost:%s', port)
    IOLoop.current().start()


if __name__ == '__main__':
    main()
