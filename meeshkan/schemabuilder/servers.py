from openapi_typed import Server
from http_types import Request
from typing import List, Optional
from urllib.parse import urlparse


def normalize_path_if_matches(request: Request, servers: List[Server]) -> Optional[str]:
    """Check if a request matches a list of server definitions.
    If matches, return the normalized path.

    For example: for server URL `https://petstore.swagger.io/v1` and request URL
    `https://petstore.swagger.io/v1/pets`, return `/pets`.

    Arguments:
        servers {List[Server]} -- List of schema Server definitions.
        request {Request} -- HTTP request.

    Returns:
        Optional[str] -- None if no match, normalized path if matches. 
    """

    for server in servers:
        server_url = urlparse(server['url'])
        if server_url.scheme != request['protocol']:
            continue

        if server_url.netloc != request['host']:
            continue

        if not request['pathname'].startswith(server_url.path):
            continue

        return request['pathname'][len(server_url.path):]

    return None
