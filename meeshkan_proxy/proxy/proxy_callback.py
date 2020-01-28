import tornado.tcpserver
from http_types import Request, Response


class ProxyCallback(tornado.tcpserver.TCPServer):
    def __init__(self, ssl_options: bool = None):
        super().__init__(ssl_options=ssl_options)

    def on_remove_channel(self, client_address: tuple):
        raise NotImplementedError()

    def on_request_complete(self, request: Request, response: Response):
        raise NotImplementedError()
