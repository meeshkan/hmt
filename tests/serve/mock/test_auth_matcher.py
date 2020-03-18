from hamcrest import assert_that, has_length, is_
from hamcrest.core.core.isinstanceof import instance_of
from http_types import RequestBuilder
from openapi_typed_2.openapi import OAuth2SecurityScheme

from meeshkan.serve.mock.auth_matcher import (
    match_request_to_security_scheme,
    match_to_security_schemes,
)
from meeshkan.serve.mock.matcher import truncate_path
from meeshkan.serve.mock.specs import load_specs

spec = load_specs("tests/serve/mock/schemas/nordea")[0]

spec_petstore = load_specs("tests/serve/mock/schemas/petstore")[0]

req = RequestBuilder.from_url("https://api.nordeaopenbanking.com/personal/v4/authorize")


def test_truncate_path():
    truncated = truncate_path(req.pathname, spec.api, req)
    assert truncated == "/v4/authorize"


def test_match_to_oauth():
    match = match_request_to_security_scheme(req, spec)
    assert_that(match, instance_of(OAuth2SecurityScheme))


def test_match_to_security_schemes():
    matches = match_to_security_schemes(req, (spec, spec_petstore))
    assert_that(matches, has_length(1))
    _, matched_spec = matches[0]
    assert_that(matched_spec, is_(spec))
