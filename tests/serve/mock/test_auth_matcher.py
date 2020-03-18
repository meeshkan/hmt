from http_types import Request, RequestBuilder
from openapi_typed_2.openapi import OAuth2SecurityScheme

from meeshkan.serve.mock.auth_matcher import (
    match_request_to_security_scheme,
    matches_to_oauth2,
)
from meeshkan.serve.mock.matcher import truncate_path
from meeshkan.serve.mock.specs import load_specs

spec = load_specs("tests/serve/mock/schemas/nordea")[0]


req = RequestBuilder.from_url("https://api.nordeaopenbanking.com/personal/v4/authorize")


def test_truncate_path():
    truncated = truncate_path(req.pathname, spec.api, req)
    assert truncated == "/v4/authorize"


def test_match_to_oauth():
    match = match_request_to_security_scheme(req, spec)
    assert match is not None
    assert isinstance(match, OAuth2SecurityScheme)
