from hamcrest import assert_that, has_entry, instance_of, is_, matches_regexp
from http_types import RequestBuilder, Response

from hmt.serve.mock.matcher import truncate_path
from hmt.serve.mock.security import (
    match_request_to_security_scheme,
    match_to_security_schemes,
)
from hmt.serve.mock.specs import load_specs

spec = load_specs("tests/serve/mock/schemas/nordea")[0].api

spec_petstore = load_specs("tests/serve/mock/schemas/petstore")[0].api

redirect_uri = "https://example.com/callback"
state = "my-state"
req = RequestBuilder.from_url(
    f"https://api.nordeaopenbanking.com/personal/v4/authorize?redirect_uri={redirect_uri}&state={state}"
)


def test_truncate_path():
    truncated = truncate_path(req.pathname, spec, req)
    assert truncated == "/v4/authorize"


def test_match_to_oauth():
    match = match_request_to_security_scheme(req, spec)
    assert_that(match, instance_of(Response))


def test_match_to_security_schemes():
    match = match_to_security_schemes(req, (spec, spec_petstore))
    assert_that(match, instance_of(Response))
    assert_that(match.statusCode, is_(302))
    expected_redirect = r"^{uri}\?code=\w+".format(uri=redirect_uri)
    assert_that(match.headers, has_entry("location", matches_regexp(expected_redirect)))


def test_match_to_nonmatching_security():
    match = match_to_security_schemes(req, (spec_petstore,))
    assert_that(match, is_(None))
