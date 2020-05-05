import collections
import typing
import urllib.parse

from hmt.serve.utils.http_utils import split_path

RoutingInfo = collections.namedtuple(
    "RoutingInfo", ["host", "hostname", "path", "scheme", "port"]
)


def get_port(scheme: str, port: typing.Optional[int]) -> int:
    if port is None:
        if scheme == "https":
            return 443
        elif scheme == "http":
            return 80
        else:
            raise AttributeError("Unsupported scheme {}".format(scheme))

    return port


class Routing:
    def route(
        self, path: str, headers: typing.Dict, inbound_scheme="http"
    ) -> RoutingInfo:
        raise NotImplementedError()


class PathRouting(Routing):
    def route(
        self, path: str, headers: typing.Dict, inbound_scheme="http"
    ) -> RoutingInfo:
        splits = split_path(path)
        url = urllib.parse.urlsplit("{}//{}".format(splits[0], splits[1]))
        path = "/" + "/".join(splits[2:])
        return RoutingInfo(
            path=path,
            host=splits[1],
            hostname=url.hostname,
            port=get_port(url.scheme, url.port),
            scheme=url.scheme,
        )


class HeaderRouting(Routing):
    def route(
        self, path: str, headers: typing.Dict, inbound_scheme="http"
    ) -> RoutingInfo:
        url = urllib.parse.urlsplit("//{}".format(headers["Host"]))
        scheme = (
            headers["X-Meeshkan-Scheme"]
            if "X-Meeshkan-Scheme" in headers
            else headers["x-hmt-scheme"]
            if "x-hmt-scheme" in headers
            else inbound_scheme
        )
        return RoutingInfo(
            path=path,
            host=headers["Host"],
            hostname=url.hostname,
            port=get_port(scheme, url.port),
            scheme=scheme,
        )


class StaticRouting(Routing):
    def __init__(self, target_address):
        self._url = urllib.parse.urlsplit(target_address)
        self._host = (
            "{}:{}".format(self._url.hostname, self._url.port)
            if self._url.port
            else self._url.hostname
        )

    def route(
        self, path: str, headers: typing.Dict, inbound_scheme="http"
    ) -> RoutingInfo:
        return RoutingInfo(
            path=path,
            host=self._host,
            hostname=self._url.hostname,
            port=get_port(self._url.scheme, self._url.port),
            scheme=self._url.scheme,
        )
