import logging
import os

import click
import tornado.ioloop
import yaml

from meeshkan_proxy.proxy.proxy import RecordProxy, MockProxy
from meeshkan_proxy.utils.data_callback import RequestLoggingCallback

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
def record(log_dir, schema_dir):
    logger.info('Starting Meeshkan proxy in recording mode')
    with RequestLoggingCallback(recording=True, log_dir=log_dir, schema_dir=schema_dir) as callback:
        server = RecordProxy(callback)
        server.listen(8899)
        tornado.ioloop.IOLoop.instance().start()


@main.command()
@click.option('--mock_server', default="http://localhost:8000", help='Mocking server address')
def mock(mock_server):
    logger.info('Starting Meeshkan proxy in mocking mode')
    with RequestLoggingCallback() as callback:
        server = MockProxy(callback, mock_server)
        server.listen(8899)
        tornado.ioloop.IOLoop.instance().start()


if __name__ == '__main__':
    main()
