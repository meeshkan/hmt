from tools.meeshkan_server import make_mocking_app

import pytest
import json

@pytest.fixture
def app():
    return make_mocking_app('tests/server/mock/callbacks', 'replay', 'tests/server/mock/github_recordings', '/dev/null')

@pytest.mark.gen_test
@pytest.mark.skip("For now there is a problem testing this because of the hosts")
def test_mocking_server_github(http_client, base_url):
    response = yield http_client.fetch(base_url+'/users/repos')
    assert response.code == 200
    rb = json.loads(response.body)
    assert type(rb) == type([])
    assert len(rb) > 0
    for repo in rb:
        assert type(repo['clone_url']) == type("")
