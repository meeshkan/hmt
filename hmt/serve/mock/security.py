from typing import Optional, Sequence

from http_types import Request, Response
from openapi_typed_2.openapi import OAuth2SecurityScheme, OpenAPIObject

from .matcher import truncate_path


def generate_code():
    return "xyz"


def gen_authflow_response(req: Request):
    if "redirect_uri" not in req.query:
        return Response(body="", statusCode=400, headers={})
    redirect_uri = req.query["redirect_uri"]

    redirect_uri = (
        redirect_uri if isinstance(redirect_uri, str) else "".join(redirect_uri)
    )

    code = generate_code()

    redirect_uri = f"{redirect_uri}?code={code}"

    if "state" in req.query:
        state = req.query["state"]
        redirect_uri = f"{redirect_uri}&state={state}"

    headers = dict(location=redirect_uri)
    return Response(body="", statusCode=302, headers=headers)


def matches_to_oauth2(
    req: Request, truncated_path: str, scheme: OAuth2SecurityScheme
) -> Optional[Response]:
    flows = scheme.flows

    if flows.authorizationCode is not None:
        auth_flow = flows.authorizationCode

        if truncated_path == auth_flow.authorizationUrl:
            return gen_authflow_response(req)

    # TODO Other flows
    return None


def match_request_to_security_scheme(
    req: Request, spec: OpenAPIObject
) -> Optional[Response]:
    """Match request to an OpenAPI document's security schemes if present.

    Arguments:
        req {Request} -- HttpRequest
        spec {OpenAPIObject} -- OpenAPI document

    Returns:
        Optional[Response] -- [description]
    """
    components = spec.components

    if components is None or components.securitySchemes is None:
        return None

    security_schemes = components.securitySchemes

    truncated_path = truncate_path(req.pathname, spec, req)

    for _, scheme in security_schemes.items():
        if isinstance(scheme, OAuth2SecurityScheme):
            maybe_response = matches_to_oauth2(req, truncated_path, scheme)
            if maybe_response is not None:
                return maybe_response
    return None


def match_to_security_schemes(
    req: Request, specs: Sequence[OpenAPIObject]
) -> Optional[Response]:

    matches_iterator = (
        match
        for spec in specs
        for match in (match_request_to_security_scheme(req, spec),)
        if match is not None
    )

    # Return first match when found, otherwise None
    return next(matches_iterator, None)
