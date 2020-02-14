import requests

#API_URL = 'https://sandbox.apis.op-palvelut.fi/'
API_URL = 'http://localhost:8000/https/sandbox.apis.op-palvelut.fi/'

ACCOUNTS_HEADERS = {
    'x-api-key': 'ZoStul8nNuwq1SYCzSrLcO1wAj4Tyf7x',
    'x-request-id': "12345",
    'x-session-id': "12345",
    'authorization': "Bearer 6c18c234b1b18b1d97c7043e2e41135c293d0da9",
    'x-authorization': "6c18c234b1b18b1d97c7043e2e41135c293d0da9",
}
#
PAYMENTS_HEADERS = {
    'x-api-key': 'ZoStul8nNuwq1SYCzSrLcO1wAj4Tyf7x',
    'x-request-id': "12345",
    'x-session-id': "12345",
    # 'authorization': "Bearer 6c18c234b1b18b1d97c7043e2e41135c293d0da9",
    'x-authorization': "6c18c234b1b18b1d97c7043e2e41135c293d0da9",
}


def get_accounts():
    return requests.get(API_URL + '/accounts/v3/accounts', headers=ACCOUNTS_HEADERS).json()['accounts']


def init_payment(payer_iban, receiver_iban, amount):
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
    url = API_URL + '/v1/payments/initiate'
    response = requests.post(url, headers=PAYMENTS_HEADERS, json=body)
    return response.json()

def confirm_payment(payment_id):
    body = {
            'paymentId': payment_id
        }
    url = API_URL + '/v1/payments/confirm'
    response = requests.post(url, headers=PAYMENTS_HEADERS, json=body)
    return  response.json()


def test_opbank():
    requests.delete("http://localhost:8888/admin/storage")

    # payer_iban = 'FI8359986950002741'
    # receiver_iban = 'FI4859986920215738'

    payer_iban = 'FI3959986920207073'
    receiver_iban = 'FI2350009421535899'
    amount = 5

    accounts = get_accounts()
    print('Account list before payment: {}'.format(accounts))

    payer_account = next((account for account in accounts if account['identifier'] == payer_iban))
    receiver_account = next((account for account in accounts if account['identifier'] == receiver_iban))

    assert 2215.81 == payer_account['balance']
    assert 0 == receiver_account['balance']


    payment = init_payment(payer_iban, receiver_iban, amount)
    payment_id = payment['paymentId']
    print("Created payment {}".format(payment))

    accounts = get_accounts()
    print('Account list after payment initiated: {}'.format(accounts))

    payer_account = next((account for account in accounts if account['identifier'] == payer_iban))
    receiver_account = next((account for account in accounts if account['identifier'] == receiver_iban))
    assert 2215.81 == payer_account['balance']
    assert 0 == receiver_account['balance']

    confirmation = confirm_payment(payment_id)

    accounts = get_accounts()
    print('Account list after payment confirmed: {}'.format(accounts))

    payer_account = next((account for account in accounts if account['identifier'] == payer_iban))
    receiver_account = next((account for account in accounts if account['identifier'] == receiver_iban))
    assert 2210.81 == payer_account['balance']
    assert 5 == receiver_account['balance']



