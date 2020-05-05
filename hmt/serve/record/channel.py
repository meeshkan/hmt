import collections
import json
import logging
import socket
import typing
from enum import Enum
from urllib import parse

from http_types import Response
from http_types.utils import RequestBuilder
from tornado.iostream import IOStream, SSLIOStream, StreamClosedError

from hmt.serve.utils.routing import Routing

from ..utils.http_utils import response_from_bytes
from .proxy_callback import ProxyCallback

logger = logging.getLogger(__name__)


class ConnectionState(Enum):
    CLOSED = 0
    CONNECTING = 1
    CONNECTED = 2
    WRITING = 3


RequestInfo = collections.namedtuple(
    "RequestInfo", ["data", "scheme", "target_host", "target_port"]
)


class StreamWrapper:
    def __init__(
        self,
        stream: IOStream,
        close_callback: typing.Callable,
        queue_on_connecting: bool,
    ):
        self._queue = []
        self._stream = stream
        self._state = ConnectionState.CONNECTING

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
        if not data:
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
                logger.warning("Server stream closed unexpectedly")
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
    def __init__(
        self,
        proxy_callback: ProxyCallback,
        stream: IOStream,
        client_address: tuple,
        router: Routing,
    ):
        self._proxy_calback = proxy_callback
        self._router = router

        self._client_stream = StreamWrapper(stream, self.on_client_close, False)
        self._client_stream.on_connect(self.on_client_read)

        self._server_stream = None
        self._client_address = client_address
        self._request = None
        self._response = list()
        self._content_length = None
        self._recieved_bytes = 0

    def on_request(self, data: bytes) -> RequestInfo:
        req_lines = data.decode("utf-8").split("\r\n")
        method, fullpath, protocol = req_lines[0].split(" ")
        parsed_fullpath = parse.urlparse(fullpath)
        query = parse.parse_qs(parsed_fullpath.query)

        headers = {}
        host_line: int = 0
        body_start: int = 0
        last_line: int = 0
        for line in req_lines[1:]:
            last_line += 1
            if not line:
                break
            else:
                header, value = line.split(": ")
                if header.lower() == "host":
                    host_line = last_line
                    headers["Host"] = value
                else:
                    headers[header] = value

        body_start = last_line + 1
        body = []
        # TODO: @Nikolay, is cur_id correct?
        for body_line in range(body_start, len(req_lines)):
            if req_lines[body_line]:
                body.append(req_lines[body_line])

        body = "\r\n".join(body)

        route_info = self._router.route(parsed_fullpath.path, headers)
        fullpath = (
            "{}?{}".format(route_info.path, parsed_fullpath.query)
            if query
            else route_info.path
        )

        req_lines[0] = " ".join((method, fullpath, protocol))
        req_lines[host_line] = "Host: {}".format(route_info.host)
        headers["Host"] = route_info.host

        data = "\r\n".join(req_lines).encode("utf-8")

        # ignoring type due to this error
        """
          46:34 - error: Argument of type 'str' cannot be assigned to parameter 'method' of type 'Literal['connect', 'head', 'trace', 'options', 'delete', 'patch', 'post', 'put', 'get']'
          'str' cannot be assigned to 'Literal['connect']'
          'str' cannot be assigned to 'Literal['head']'
          'str' cannot be assigned to 'Literal['trace']'
          'str' cannot be assigned to 'Literal['options']'
          'str' cannot be assigned to 'Literal['delete']'
        """
        self._request = RequestBuilder.from_dict(
            dict(
                method=method.lower(),
                host=route_info.host,
                path=fullpath,
                pathname=route_info.path,
                protocol=route_info.scheme,
                query=query,
                body=body,
                bodyAsJson=json.loads(body) if body else {},
                headers=headers,
            )
        )

        return RequestInfo(
            data=data,
            scheme=route_info.scheme,
            target_host=route_info.hostname,
            target_port=route_info.port,
        )

    def on_response_chunk(self, data: bytes):
        if len(self._response) == 0:
            resp_lines = data.split(b"\r\n")
            for line in resp_lines[1:]:
                res = line.split(b": ")
                if len(res) == 2:
                    header, value = res[0].decode("utf-8"), res[1].decode("utf-8")
                    if header == "Content-Length":
                        self._content_length = int(value)
                        break

        self._response.append(data)
        self._recieved_bytes += len(data)

        logger.debug(
            "[%s] Received response chunk %d bytes out of %d",
            self._client_address,
            self._recieved_bytes,
            self._content_length or 0,
        )

    def flush(self, check_length=True):
        if len(self._response) > 0 and self._request is not None:
            if (
                not check_length
                or self._content_length is None
                or self._recieved_bytes >= self._content_length
            ):
                logger.debug(
                    "[%s] Flushing request, received %d bytes out of %d",
                    self._client_address,
                    self._recieved_bytes,
                    self._content_length or 0,
                )

                resp = b"".join(self._response)
                resp = response_from_bytes(resp)
                body = resp.data.decode("utf-8")

                resp = Response(
                    statusCode=resp.status,
                    body=body,
                    bodyAsJson=json.loads(body),
                    headers=dict(resp.getheaders()),
                    timestamp=None,
                )

                self._proxy_calback.on_request_complete(self._request, resp)

                self._request = None
                self._response = []
                self._content_length = None
                self._recieved_bytes = 0
        else:
            logger.debug(
                '[%s] Trying to flush incomplete data, request "%s", response chunks %d',
                self._client_address,
                str(self._request),
                len(self._response),
            )

    def on_server_read(self, data):
        self.on_response_chunk(data)
        self._client_stream.write(data)

    def on_client_read(self, data):
        self.flush()

        request_info = self.on_request(data)

        logger.debug(
            "[%s] Got request for %s://%s:%s",
            self._client_address,
            request_info.scheme,
            request_info.target_host,
            request_info.target_port,
        )

        if self._server_stream is None:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
            stream = (
                SSLIOStream(s, ssl_options={})
                if request_info.scheme == "https"
                else IOStream(s)
            )
            stream.connect(
                (request_info.target_host, request_info.target_port),
                self.on_server_connect,
                server_hostname=request_info.target_host,
            )
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
            self._client_stream.write(b"")

    def on_client_close(self):
        self._client_stream.close()
        if (
            self._server_stream is None
            or self._server_stream.state == ConnectionState.CLOSED
        ):
            self.remove_channel()
        else:
            self._server_stream.write(b"")

    @property
    def server_state(self):
        return (
            ConnectionState.CLOSED
            if self._server_stream is None
            else self._server_stream.state
        )

    @property
    def client_state(self):
        return self._client_stream.state
