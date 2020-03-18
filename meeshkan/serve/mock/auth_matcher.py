from typing import Optional, Union, Sequence, Tuple

from http_types import Request
from openapi_typed_2.openapi import (
    AuthorizationCodeOAuthFlow,
    OAuth2SecurityScheme,
    SecurityScheme,
)

from .matcher import truncate_path
from .specs import OpenAPISpecification


def matches_to_oauth2(
    truncated_path: str, scheme: OAuth2SecurityScheme
) -> Optional[Union[AuthorizationCodeOAuthFlow]]:
    flows = scheme.flows

    if flows.authorizationCode is not None:
        auth_flow = flows.authorizationCode
        if (
            auth_flow.authorizationUrl == truncated_path
            or auth_flow.tokenUrl == truncated_path
            or auth_flow.refreshUrl == truncated_path
        ):
            return auth_flow

    # TODO Other flows
    return None


def match_request_to_security_scheme(
    req: Request, spec: OpenAPISpecification
) -> Optional[SecurityScheme]:
    components = spec.api.components

    if components is None or components.securitySchemes is None:
        return None

    security_schemes = components.securitySchemes

    truncated_path = truncate_path(req.pathname, spec.api, req)

    for _, scheme in security_schemes.items():
        if isinstance(scheme, OAuth2SecurityScheme):
            if matches_to_oauth2(truncated_path, scheme):
                return scheme

    return None


def match_to_security_schemes(
    req: Request, specs: Sequence[OpenAPISpecification]
) -> Sequence[Tuple[SecurityScheme, OpenAPISpecification]]:
    return [
        (security_match, spec)
        for spec in specs
        for security_match in (match_request_to_security_scheme(req, spec),)
        if security_match is not None
    ]
