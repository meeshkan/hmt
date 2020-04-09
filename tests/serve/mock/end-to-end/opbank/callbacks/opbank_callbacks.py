import copy

from meeshkan.serve.mock.callbacks import callback


@callback("sandbox.apis.op-palvelut.fi", "post", "/v1/payments/initiate", format="json")
def initiate(request_body, response_body, storage):
    storage.default[response_body["paymentId"]] = request_body
    return response_body


@callback("sandbox.apis.op-palvelut.fi", "post", "/v1/payments/confirm", format="json")
def confirm(request_body, response_body, storage):
    payment_info = storage.default[response_body["paymentId"]]
    storage.default[payment_info["receiverIban"]] = (
        storage.default.get(payment_info["receiverIban"], 0) + payment_info["amount"]
    )
    storage.default[payment_info["payerIban"]] = (
        storage.default.get(payment_info["payerIban"], 0) - payment_info["amount"]
    )
    return response_body


@callback("sandbox.apis.op-palvelut.fi", "get", "/accounts/v3/accounts", format="json")
def accounts(request_body, response_body, storage):
    response_body_new = copy.deepcopy(response_body)
    for account in response_body_new["accounts"]:
        account["balance"] += storage.default.get(account["identifier"], 0)
    return response_body_new
