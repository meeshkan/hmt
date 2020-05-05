from typing import List

from hamcrest import *
from http_types import RequestBuilder
from openapi_typed_2 import Server

from hmt.build.servers import normalize_path_if_matches

petstore_req = RequestBuilder.from_url("https://petstore.swagger.io/v1/pets")

petstore_server = Server(
    description=None, variables=None, _x=None, url="https://petstore.swagger.io/v1"
)


def test_normalize_path_for_match():
    norm_pathname = normalize_path_if_matches(petstore_req, [petstore_server])
    assert_that(norm_pathname, is_("/pets"))


def test_no_match():
    req_no_match = RequestBuilder.from_url("https://petstore.swagger.io/v2/pets")
    norm_pathname = normalize_path_if_matches(req_no_match, [petstore_server])
    assert_that(norm_pathname, is_(None))
