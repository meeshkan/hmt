import datetime
from typing import Optional, Sequence, Tuple
from urllib.parse import urlparse

from http_types import Request
from openapi_typed_2 import OpenAPIObject, PathItem

from hmt.serve.mock.specs import OpenAPISpecification


def matches(
    path: Sequence[str], path_item_key: str, path_item: PathItem, method: str
) -> int:
    if getattr(path_item, method, None) is None:
        return 0

    path_item_key_list = [x for x in path_item_key.split("/") if x != ""]
    score = 1
    if len(path) != len(path_item_key_list):
        return 0
    for path_el, path_item_key_el in zip(path, path_item_key_list):

        if path_item_key_el[0] == "{" and path_item_key_el[-1] == "}":
            continue
        elif path_el == path_item_key_el:
            score += 1
        else:
            return 0
    return score


def match_urls(protocol: str, host: str, o: OpenAPIObject) -> Sequence[str]:
    """Finds mock URLs that match a given protocol and host.

    Arguments:
        protocol {str} -- like http or https
        host {str} -- like api.foo.com
        o {OpenAPIObject} -- schema from which the mock URLs are taken

    Returns:
        A list of URLs that match the OpenAPI spec.
    """
    servers = o.servers
    if servers is None:
        return []
    #### if the openapi mock url has no scheme,
    #### we ignore the incoming scheme and treat the url as the host
    #### not sure if this is the right decision,
    #### but it deals with a realistic outcome in certain schemas
    return [
        server.url
        for server in servers
        if (
            (urlparse(server.url).scheme in ["", None])
            or (urlparse(server.url).scheme == protocol)
        )
        and (
            (server.url.split("/")[0] == host) or (urlparse(server.url).netloc == host)
        )
    ]


def cut_path(paths: Sequence[str], path: str) -> str:
    return (
        path
        if len(paths) == 0
        else path[len(paths[0]) :]
        if path[: len(paths[0])] == paths[0]
        else cut_path(paths[1:], path)
    )


def remove_trailing_slash(s: str) -> str:
    return s if len(s) == 0 else s[:-1] if s[-1] == "/" else s


def truncate_path(path: str, o: OpenAPIObject, i: Request,) -> str:
    return cut_path(
        [
            remove_trailing_slash(urlparse(u).path)
            for u in match_urls(i.protocol.value, i.host, o)
        ],
        path,
    )


def match_request_to_openapi(
    req: Request, specs: Sequence[OpenAPISpecification]
) -> Tuple[Optional[str], Optional[OpenAPISpecification]]:
    def _match_path(oai: OpenAPIObject) -> Optional[str]:
        path = [x for x in truncate_path(req.pathname, oai, req).split("/") if x != ""]
        best_path: Optional[str] = None
        best_score = 0

        for pathname, path_item in oai.paths.items():
            score = matches(path, pathname, path_item, req.method.value)
            if score > 0 and score > best_score:
                best_path = pathname
                best_score = score

        return best_path

    specs_with_matching_urls = (
        spec
        for spec in specs
        if len(match_urls(req.protocol.value, req.host, spec.api)) > 0
    )
    for spec in specs_with_matching_urls:
        path = _match_path(spec.api)
        if path is not None:
            return path, spec

    return None, None
