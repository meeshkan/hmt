from http_types import Request, Response
from http_types.utils import RequestBuilder, ResponseBuilder

from meeshkan.server.server.callbacks import callback_manager
from meeshkan.server.server.storage import storage_manager


def test_no_callback():
    callback_manager.load("tests/server/server/callbacks")

    request = RequestBuilder.from_dict(
        dict(
            method="get",
            host="api.com",
            pathname="/nothing",
            query={},
            body="",
            protocol="http",
            bodyAsJson={},
            headers={},
        )
    )

    response = ResponseBuilder.from_dict(
        dict(statusCode=200, body="", bodyAsJson={}, headers={})
    )

    new_response = callback_manager(request, response)

    assert response == new_response


def test_json():
    callback_manager.load("tests/server/server/callbacks")
    storage_manager.clear()

    request = RequestBuilder.from_dict(
        dict(
            method="post",
            host="api.com",
            pathname="/counter",
            query={},
            body="",
            protocol="http",
            bodyAsJson={},
            headers={},
        )
    )

    response = ResponseBuilder.from_dict(
        dict(statusCode=200, body="", bodyAsJson={"field": "value"}, headers={})
    )

    new_response = callback_manager(request, response)

    assert 1 == new_response.bodyAsJson["count"]
    assert "value" == new_response.bodyAsJson["field"]
    assert "count" in new_response.body

    request_set = RequestBuilder.from_dict(
        dict(
            method="post",
            host="api.com",
            pathname="/counter",
            query={},
            body="",
            protocol="http",
            bodyAsJson={"set": 10},
            headers={},
        )
    )

    new_response = callback_manager(request_set, response)

    assert 10 == new_response.bodyAsJson["count"]
    assert "value" == new_response.bodyAsJson["field"]
    assert "count" in new_response.body

    new_response = callback_manager(request, response)
    assert 11 == new_response.bodyAsJson["count"]
    assert "value" == new_response.bodyAsJson["field"]
    assert "count" in new_response.body


def test_text():
    callback_manager.load("tests/server/server/callbacks")
    storage_manager.clear()

    request = RequestBuilder.from_dict(
        dict(
            method="get",
            host="api.com",
            pathname="/text_counter",
            query={"set": 10},
            body="",
            protocol="http",
            bodyAsJson={},
            headers={},
        )
    )

    response = ResponseBuilder.from_dict(
        dict(statusCode=200, body="Called", bodyAsJson={}, headers={})
    )

    new_response = callback_manager(request, response)

    assert "Called 10 times" == new_response.body


def test_json_full():
    callback_manager.load("tests/server/server/callbacks")
    storage_manager.clear()

    request = RequestBuilder.from_dict(
        dict(
            method="get",
            host="another.api.com",
            pathname="/echo",
            query={"message": "Hello"},
            body="",
            protocol="http",
            bodyAsJson={},
            headers={},
        )
    )

    response = ResponseBuilder.from_dict(
        dict(statusCode=200, body="", bodyAsJson={"field": "value"}, headers={})
    )

    new_response = callback_manager(request, response)

    assert "Hello" == new_response.bodyAsJson["message"]
    assert "value" == new_response.headers["X-Echo-Header"]


def test_text_full():
    callback_manager.load("tests/server/server/callbacks")
    storage_manager.clear()

    request = RequestBuilder.from_dict(
        dict(
            method="post",
            host="another.api.com",
            pathname="/echo",
            query={},
            protocol="http",
            body="Hello",
            bodyAsJson={},
            headers={},
        )
    )

    response = ResponseBuilder.from_dict(
        dict(statusCode=200, body="", bodyAsJson={"field": "value"}, headers={})
    )

    new_response = callback_manager(request, response)

    assert "Hello" == new_response.body
    assert "value" == new_response.headers["X-Echo-Header"]
