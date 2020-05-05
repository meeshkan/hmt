import logging

import tornado.ioloop
from http_types import Request, Response

from hmt.serve.utils.data_callback import RequestLoggingCallback
from hmt.serve.utils.routing import HeaderRouting

from .channel import Channel
from .proxy_callback import ProxyCallback

logger = logging.getLogger(__name__)


class ProxyBase(ProxyCallback):
    def __init__(self, data_callback, router, ssl_options=None):
        super().__init__(ssl_options=ssl_options)
        self._data_callback = data_callback
        self._channels = dict()
        self._router = router

    def handle_stream(self, stream, address):
        logger.debug(
            "Creating channel for new connection from client {}".format(address)
        )
        self._channels[address] = self._create_channel(stream, address)

    def on_remove_channel(self, client_address):
        channel = self._channels[client_address]
        del self._channels[client_address]
        del channel

    def _create_channel(self, stream, client_address):
        raise NotImplementedError()

    def on_request_complete(self, request: Request, response: Response):
        pass

    @property
    def router(self):
        return self._router


class RecordProxy(ProxyBase):
    def __init__(self, data_callback, router, ssl_options=None):
        super().__init__(data_callback, router, ssl_options=ssl_options)

    def _create_channel(self, stream, client_address):
        return Channel(self, stream, client_address, self.router)

    def on_request_complete(self, request: Request, response: Response):
        self._data_callback.log(request, response)


class RecordProxyRunner:
    def __init__(
        self, port, log_dir, specs_dir, routing=HeaderRouting(), mode=None,
    ):
        self._port = port
        self._log_dir = log_dir
        self._specs_dir = specs_dir
        self._routing = routing
        self._mode = mode

    def run(self):

        logger.info("Starting Meeshkan record on http://localhost:%s", self._port)
        logger.info(
            "Spec generation mode is %s",
            self._mode.name.lower() if self._mode else "disabled",
        )
        with RequestLoggingCallback(
            log_dir=self._log_dir, specs_dir=self._specs_dir, update_mode=self._mode
        ) as callback:
            server = RecordProxy(callback, self._routing)
            server.listen(self._port)
            logger.info("Meeshkan is running")
            tornado.ioloop.IOLoop.instance().start()
