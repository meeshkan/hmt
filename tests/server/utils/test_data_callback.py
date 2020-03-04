import json
import os
import shutil
from unittest.mock import patch

from http_types import Response, Request, RequestBuilder, ResponseBuilder, HttpExchangeReader

from meeshkan import UpdateMode
from meeshkan.server.utils.data_callback import RequestLoggingCallback


def test_request_logging():
    if os.path.exists('./tests/tmp'):
        shutil.rmtree('./tests/tmp')

    request = RequestBuilder.from_dict(dict(method='get',
                      host='another.api.com',
                      pathname='/echo',
                      query={'message': 'Hello'},
                      body='',
                      bodyAsJson={},
                      path='/echo',
                      protocol='http',
                      headers={}))
    response = ResponseBuilder.from_dict(dict(statusCode=200, body='{"message": "hello"}', bodyAsJson={"message": "hello"},
                        headers={}))

    with RequestLoggingCallback(log_dir='./tests/tmp/logs', specs_dir='./tests/tmp/specs',
                                update_mode=UpdateMode.MIXED) as data_callback:
        data_callback.log(request, response)

    assert os.path.exists('./tests/tmp/logs/another.api.com-recordings.jsonl')
    assert os.path.exists('./tests/tmp/specs/another.api.com_mixed.yaml')

    request = RequestBuilder.from_dict(dict(method='get',
                      host='api.com',
                      pathname='/echo',
                      query={'message': 'Hello'},
                      body='',
                      protocol='http',
                      headers={}))
    response = ResponseBuilder.from_dict(dict(statusCode=200, body='{"message": "hello"}', bodyAsJson={"message": "hello"},
                        headers={}))

    with RequestLoggingCallback(log_dir='./tests/tmp/logs', specs_dir='./tests/tmp/specs',
                                update_mode=UpdateMode.GEN) as data_callback:
        data_callback.log(request, response)

    expected_recordings_path = './tests/tmp/logs/api.com-recordings.jsonl'
    assert os.path.exists(expected_recordings_path)
    assert os.path.exists('./tests/tmp/specs/api.com_gen.yaml')

    with open(expected_recordings_path, 'r') as f:
        data = [x for x in f.read().split('\n') if x != '']
        assert 1 == len(data)
        http_exchange = HttpExchangeReader.from_json(data[0])
        assert request == http_exchange.request
        assert response == http_exchange.response


    shutil.rmtree('./tests/tmp')

    with RequestLoggingCallback(log_dir='./tests/tmp/logs', specs_dir='./tests/tmp/specs',
                                update_mode=None) as data_callback:
        data_callback.log(request, response)

    assert os.path.exists(expected_recordings_path)
    assert 0 == len(os.listdir('./tests/tmp/specs'))


    shutil.rmtree('./tests/tmp')
