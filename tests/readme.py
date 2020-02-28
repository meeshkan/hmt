from openapi_typed import OpenAPIObject
import meeshkan
from typing import List
import json
from http_types import HttpExchange, Request, Response, RequestBuilder


def read_http_exchanges() -> List[HttpExchange]:
    """Read HTTP exchanges from the source of your choice.
    """
    request: Request = RequestBuilder.from_url(
        "https://example.org/v1", method="get", headers={}
    )

    response: Response = Response(
        statusCode=200, body=json.dumps({"hello": "world"}), headers={}
    )

    http_exchange: HttpExchange = {"request": request, "response": response}

    return [http_exchange]


http_exchanges = read_http_exchanges()

# Build OpenAPI schema from a list of recordings
openapi: OpenAPIObject = meeshkan.build_schema_batch(http_exchanges)

# Build schema from an iterator
openapi: OpenAPIObject = meeshkan.build_schema_online(iter(http_exchanges))

# Update OpenAPI schema one `HttpExchange` at a time
http_exchange = http_exchanges[0]
openapi: OpenAPIObject = meeshkan.update_openapi(openapi, http_exchange)
