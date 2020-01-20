from meeshkan.__main__ import main
from .util import read_requests

requests = read_requests()


def test_build_schema():
    schema_str = main(iterator=read_requests()[:10])
    assert type(schema_str) is str
