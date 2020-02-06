import collections
import json
import logging
import os
import socket
import typing
from enum import Enum
from urllib import parse
from urllib.parse import urlsplit
from http_types import Request, Response
from tornado.iostream import IOStream, SSLIOStream, StreamClosedError

from meeshkan_proxy.proxy.proxy_callback import ProxyCallback
from meeshkan_proxy.utils.http_utils import split_path, response_from_bytes

logger = logging.getLogger(__name__)


class ConnectionState(Enum):
    CLOSED = 0
    CONNECTING = 1
    CONNECTED = 2
    WRITING = 3


RequestInfo = collections.namedtuple('RequestInfo', ['data', 'scheme', 'target_host', 'target_port'])


class StreamWrapper:
    def __init__(self, stream: IOStream, close_callback: typing.Callable, queue_on_connecting: bool):
        self._queue = []
        self._stream = stream
        self._state = ConnectionState.CONNECTING

        self._stream.set_nodelay(True)
        self._stream.set_close_callback(close_callback)
        self._queue_on_connecting = queue_on_connecting

    def on_connect(self, read_callback: typing.Callable):
        self._state = ConnectionState.CONNECTED

        try:
            self._stream.read_until_close(lambda x: None, read_callback)
        except StreamClosedError:
            self._state = ConnectionState.CLOSED

    def write(self, data: bytes):
        if self._state not in {ConnectionState.CONNECTED, ConnectionState.WRITING}:
            if self._queue_on_connecting:
                self._queue.append(data)
            return

        if self._state != ConnectionState.WRITING:
            self._do_write(data)
        else:
            self._queue.append(data)

    def _do_write(self, data):
        if data is None:
            self._state = ConnectionState.CLOSED
            try:
                self._stream.close()
            except StreamClosedError:
                pass
        else:
            self._client_state = ConnectionState.WRITING
            try:
                self._stream.write(data, callback=self._on_done_write())
            except StreamClosedError:
                logger.warning('Server stream closed unexpectedly')
                self._client_state = ConnectionState.CLOSED

    def _on_done_write(self):
        if self._queue:
            self._do_write(self._queue.pop(0))
            return
        self._client_state = ConnectionState.CONNECTED

    @property
    def stream(self):
        return self._stream

    @property
    def queue(self):
        return self._queue

    @property
    def state(self):
        return self._state

    def close(self):
        self._state = ConnectionState.CLOSED


class Channel:
    def __init__(self, proxy_callback: ProxyCallback, stream: IOStream, client_address: tuple):
        self._proxy_calback = proxy_callback

        self._client_stream = StreamWrapper(stream, self.on_client_close, False)
        self._client_stream.on_connect(self.on_client_read)

        self._server_stream = None
        self._client_address = client_address
        self._request = None
        self._response = list()
        self._content_length = None
        self._recieved_bytes = 0

    def on_request(self, data: bytes) -> RequestInfo:
        req_lines = data.decode('utf-8').split('\r\n')
        method, fullpath, protocol = req_lines[0].split(' ')
        parsed_fullpath = parse.urlparse(fullpath)
        splits = split_path(parsed_fullpath.path)
        scheme, host = splits[0], splits[1]
        path = os.path.join('/', *splits[2:])
        query = parse.parse_qs(parsed_fullpath.query)

        fullpath = "{}?{}".format(path, parsed_fullpath.query) if query else path

        req_lines[0] = ' '.join((method, fullpath, protocol))

        headers = {}
        for line_id, line in enumerate(req_lines[1:]):
            if not line:
                break
            else:
                header, value = line.split(': ')
                if header == 'Host':
                    value = host
                    req_lines[line_id + 1] = 'Host: {}'.format(host)
                headers[header] = value

        body = []
        for body_line in range(line_id + 2, len(req_lines)):
            if req_lines[body_line]:
                body.append(req_lines[body_line])

        body = '\r\n'.join(body)

        data = '\r\n'.join(req_lines)
        data = data.encode('utf-8')

        self._request = Request(method=method.lower(),
                                host=host,
                                path=fullpath,
                                pathname=path,
                                protocol=scheme,
                                query=query,
                                body=body,
                                bodyAsJson="",
                                headers=headers)

        return RequestInfo(data=data, scheme=scheme, target_host=host, target_port=443 if scheme == 'https' else 80)

    def on_response_chunk(self, data: bytes):
        if len(self._response) == 0:
            resp_lines = data.split(b'\r\n')
            for line in resp_lines[1:]:
                res = line.split(b': ')
                if len(res) == 2:
                    header, value = res[0].decode('utf-8'), res[1].decode('utf-8')
                    if header == 'Content-Length':
                        self._content_length = int(value)
                        break

        self._response.append(data)
        self._recieved_bytes += len(data)

        logger.debug('[%s] Received response chunk %d bytes out of %d', self._client_address,
                     self._recieved_bytes, self._content_length or 0)

    def flush(self, check_length=True):
        if len(self._response) > 0 and self._request is not None:
            if not check_length or self._content_length is None or self._recieved_bytes >= self._content_length:
                logger.debug('[%s] Flushing request, received %d bytes out of %d', self._client_address,
                             self._recieved_bytes, self._content_length or 0)

                resp = b''.join(self._response)
                resp = response_from_bytes(resp)
                body = resp.data.decode('utf-8')

                resp = Response(statusCode=resp.status, body=body, bodyAsJson=json.loads(body),
                                headers=dict(resp.getheaders()))

                self._proxy_calback.on_request_complete(self._request, resp)

                self._request = None
                self._response = []
                self._content_length = None
                self._recieved_bytes = 0
        else:
            logger.debug('[%s] Trying to flush incomplete data, request "%s", response chunks %d', self._client_address,
                         str(self._request), len(self._response))

    def on_server_read(self, data):
        self.on_response_chunk(data)
        self._client_stream.write(data)

    def on_client_read(self, data):
        self.flush()

        request_info = self.on_request(data)

        logger.debug('[%s] Got request for %s://%s:%s', self._client_address, request_info.scheme,
                     request_info.target_host, request_info.target_port)

        if self._server_stream is None:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
            stream = SSLIOStream(s, ssl_options={}) if request_info.scheme == 'https' else IOStream(s)
            stream.connect((request_info.target_host, request_info.target_port), self.on_server_connect)
            self._server_stream = StreamWrapper(stream, self.on_server_close, True)

        self._server_stream.write(request_info.data)

    def on_server_connect(self):
        self._server_stream.on_connect(self.on_server_read)
        if self._server_stream.queue:
            self._server_stream.write(self._server_stream.queue.pop(0))

    def remove_channel(self):
        self.flush(check_length=False)
        self._proxy_calback.on_remove_channel(self._client_address)

    def on_server_close(self):
        self._server_stream.close()
        if self._client_stream.state == ConnectionState.CLOSED:
            self.remove_channel()
        else:
            self._client_stream.write(None)

    def on_client_close(self):
        self._client_stream.close()
        if self._server_stream is None or self._server_stream.state == ConnectionState.CLOSED:
            self.remove_channel()
        else:
            self._server_stream.write(None)

    @property
    def server_state(self):
        return ConnectionState.CLOSED if self._server_stream is None else self._server_stream.state

    @property
    def client_state(self):
        return self._client_stream.state


class MockChannel(Channel):
    def __init__(self, proxy_callback: ProxyCallback, stream: IOStream,
                 client_address: tuple, mock_address: str):
        super().__init__(proxy_callback, stream, client_address)
        url = urlsplit(mock_address)
        self._mock_host = url.hostname
        self._mock_port = url.port
        self._mock_scheme = url.scheme

    def on_request(self, data: bytes) -> RequestInfo:
        request_info = super().on_request(data)
        return RequestInfo(data=request_info.data, target_host=self._mock_host, target_port=self._mock_port,
                           scheme=self._mock_scheme)
