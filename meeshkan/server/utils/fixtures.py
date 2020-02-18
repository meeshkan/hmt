import pytest
import requests


@pytest.fixture()
def reset_state(request):
    requests.delete("http://localhost:8888/admin/storage")
