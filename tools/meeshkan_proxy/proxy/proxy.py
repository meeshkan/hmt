import logging

from http_types import Request, Response

from meeshkan_proxy.proxy.channel import Channel, MockChannel
from meeshkan_proxy.proxy.proxy_callback import ProxyCallback

logger = logging.getLogger(__name__)


class ProxyBase(ProxyCallback):
    def __init__(self, data_callback=None, ssl_options=None):
        super().__init__(ssl_options=ssl_options)
        self._data_callback = data_callback
        self._channels = dict()

    def handle_stream(self, stream, address):
        logger.debug("Creating channel for new connection from client {}".format(address))
        self._channels[address] = self._create_channel(stream, address)

    def on_remove_channel(self, client_address):
        channel = self._channels[client_address]
        del self._channels[client_address]
        del channel

    def _create_channel(self, stream, client_address):
        raise NotImplementedError()

    def on_request_complete(self, request: Request, response: Response):
        pass


class RecordProxy(ProxyBase):
    def __init__(self, data_callback, ssl_options=None):
        super().__init__(data_callback, ssl_options=ssl_options)

    def _create_channel(self, stream, client_address):
        return Channel(self, stream, client_address)

    def on_request_complete(self, request: Request, response: Response):
        self._data_callback.log(request, response)


class MockProxy(ProxyBase):
    def __init__(self, data_callback, mock_address, ssl_options=None):
        super().__init__(data_callback, ssl_options)
        self._mock_address = mock_address

    def _create_channel(self, stream, client_address):
        return MockChannel(self, stream, client_address, self._mock_address)
