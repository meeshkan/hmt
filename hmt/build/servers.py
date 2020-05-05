from typing import List, Optional, Sequence
from urllib.parse import urlparse

from http_types import Request
from openapi_typed_2 import Server


def normalize_path_if_matches(
    request: Request, servers: Sequence[Server]
) -> Optional[str]:
    """Check if a request matches a list of mock definitions.
    If matches, return the request path normalized by the mock URL's basepath.

    For example: for matching mock URL `https://petstore.swagger.io/v1` and request URL
    `https://petstore.swagger.io/v1/pets`, return `/pets`.

    Arguments:
        servers {List[Server]} -- List of schema Server definitions.
        request {Request} -- HTTP request.

    Returns:
        Optional[str] -- None if request does not match any existing servers. Request path normalized by mock basepath otherwise.
    """

    for server in servers:
        server_url = urlparse(server.url)
        if server_url.scheme != request.protocol.value:
            continue

        if server_url.netloc != request.host:
            continue

        if not request.pathname.startswith(server_url.path):
            continue

        return request.pathname[len(server_url.path) :]

    return None
