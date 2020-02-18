import copy

from meeshkan.server.server.callbacks import callback


@callback('sandbox.apis.op-palvelut.fi', 'post', '/v1/payments/initiate', format='json')
def initiate(request_body, response_body, storage):
    storage[response_body['paymentId']] = request_body
    return response_body


@callback('sandbox.apis.op-palvelut.fi', 'post', '/v1/payments/confirm', format='json')
def confirm(request_body, response_body, storage):
    payment_info = storage[response_body['paymentId']]
    storage[payment_info['receiverIban']] = storage.get(payment_info['receiverIban'], 0) + payment_info['amount']
    storage[payment_info['payerIban']] = storage.get(payment_info['payerIban'], 0) - payment_info['amount']
    return response_body


@callback('sandbox.apis.op-palvelut.fi', 'get', '/accounts/v3/accounts', format='json')
def accounts(request_body, response_body, storage):
    response_body_new = copy.deepcopy(response_body)
    for account in response_body_new['accounts']:
        account['balance'] += storage.get(account['identifier'], 0)
    return response_body_new
