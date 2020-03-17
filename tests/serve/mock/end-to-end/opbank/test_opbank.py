import json

import pytest
from tornado.httpclient import AsyncHTTPClient, HTTPRequest

from meeshkan.serve.mock.log import Log
from meeshkan.serve.mock.scope import Scope
from meeshkan.serve.mock.server import make_mocking_app
from meeshkan.serve.mock.specs import load_specs
from meeshkan.serve.utils.routing import HeaderRouting


@pytest.fixture
def app():
    return make_mocking_app(
        "tests/serve/mock/end-to-end/opbank/callbacks",
        load_specs("tests/serve/mock/end-to-end/opbank/schemas"),
        HeaderRouting(),
        Log(Scope()),
    )


ACCOUNTS_HEADERS = {
    "Host": "sandbox.apis.op-palvelut.fi",
    "x-api-key": "ZoStul8nNuwq1SYCzSrLcO1wAj4Tyf7x",
    "x-request-id": "12345",
    "x-session-id": "12345",
    "authorization": "Bearer 6c18c234b1b18b1d97c7043e2e41135c293d0da9",
    "x-authorization": "6c18c234b1b18b1d97c7043e2e41135c293d0da9",
}
#
PAYMENTS_HEADERS = {
    "Host": "sandbox.apis.op-palvelut.fi",
    "x-api-key": "ZoStul8nNuwq1SYCzSrLcO1wAj4Tyf7x",
    "x-request-id": "12345",
    "x-session-id": "12345",
    # 'authorization': "Bearer 6c18c234b1b18b1d97c7043e2e41135c293d0da9",
    "x-authorization": "6c18c234b1b18b1d97c7043e2e41135c293d0da9",
}


"""
def get_accounts(http_client: AsyncHTTPClient, base_url: str):
    req = HTTPRequest(base_url+'/accounts/v3/accounts', headers=ACCOUNTS_HEADERS)
    ret = yield http_client.fetch(req)
    return json.loads(ret.body)['accounts']
"""

"""
def init_payment(payer_iban, receiver_iban, amount, http_client, base_url):
    body = {
        "amount": amount,
        "subject": "Client Test",
        "currency": "EUR",
        "payerIban": payer_iban,
        "valueDate": "2020-01-27T22:59:34Z",
        "receiverBic": "string",
        "receiverIban": receiver_iban,
        "receiverName": "string"
    }
    url = base_url + '/v1/payments/initiate'
    req = HTTPRequest(url, method='POST', headers=PAYMENTS_HEADERS, body=json.dumps(body))
    res = yield http_client.fetch(req)
    return json.loads(res.body)
"""

"""
def confirm_payment(payment_id, http_client: AsyncHTTPClient, base_url: str):
    body = {
            'paymentId': payment_id
        }
    url = base_url + '/v1/payments/confirm'
    req = HTTPRequest(url, headers=PAYMENTS_HEADERS, body=json.dumps(body))
    response = yield http_client.fetch(req)
    return  json.loads(response)
"""


@pytest.mark.gen_test
def test_opbank(http_client: AsyncHTTPClient, base_url: str):
    # eventually, we will want to test the line below
    # currently, however, pytest.tornado only supports creating
    # one fixture for a mock
    # requests.delete("http://localhost:8888/admin/storage")

    # payer_iban = 'FI8359986950002741'
    # receiver_iban = 'FI4859986920215738'

    payer_iban = "FI3959986920207073"
    receiver_iban = "FI2350009421535899"
    amount = 5

    ### get account
    req = HTTPRequest(base_url + "/accounts/v3/accounts", headers=ACCOUNTS_HEADERS)
    ret = yield http_client.fetch(req)
    accounts = json.loads(ret.body)["accounts"]
    print("Account list before payment: {}".format(accounts))

    payer_account = next(
        (account for account in accounts if account["identifier"] == payer_iban)
    )
    receiver_account = next(
        (account for account in accounts if account["identifier"] == receiver_iban)
    )

    assert 2215.81 == payer_account["balance"]
    assert 0 == receiver_account["balance"]

    ### init account
    body = {
        "amount": amount,
        "subject": "Client Test",
        "currency": "EUR",
        "payerIban": payer_iban,
        "valueDate": "2020-01-27T22:59:34Z",
        "receiverBic": "string",
        "receiverIban": receiver_iban,
        "receiverName": "string",
    }
    url = base_url + "/v1/payments/initiate"
    req = HTTPRequest(
        url, method="POST", headers=PAYMENTS_HEADERS, body=json.dumps(body)
    )
    res = yield http_client.fetch(req)
    payment = json.loads(res.body)

    payment_id: str = payment["paymentId"]
    print("Created payment {}".format(payment))

    ### get account
    req = HTTPRequest(base_url + "/accounts/v3/accounts", headers=ACCOUNTS_HEADERS)
    ret = yield http_client.fetch(req)
    accounts = json.loads(ret.body)["accounts"]
    print("Account list after payment initiated: {}".format(accounts))

    payer_account = next(
        (account for account in accounts if account["identifier"] == payer_iban)
    )
    receiver_account = next(
        (account for account in accounts if account["identifier"] == receiver_iban)
    )
    assert 2215.81 == payer_account["balance"]
    assert 0 == receiver_account["balance"]

    ### confirm payment
    body = {"paymentId": payment_id}
    url = base_url + "/v1/payments/confirm"
    req = HTTPRequest(
        url, method="POST", headers=PAYMENTS_HEADERS, body=json.dumps(body)
    )
    yield http_client.fetch(req)

    ### get accounts
    req = HTTPRequest(base_url + "/accounts/v3/accounts", headers=ACCOUNTS_HEADERS)
    ret = yield http_client.fetch(req)
    accounts = json.loads(ret.body)["accounts"]
    print("Account list after payment confirmed: {}".format(accounts))

    payer_account = next(
        (account for account in accounts if account["identifier"] == payer_iban)
    )
    receiver_account = next(
        (account for account in accounts if account["identifier"] == receiver_iban)
    )
    assert 2210.81 == payer_account["balance"]
    assert 5 == receiver_account["balance"]
