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
    return requests.get(API_URL + '/accounts/v3/accounts', headers=ACCOUNTS_HEADERS).json()


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


def main():
    print('Account list: {}'.format(get_accounts()))

    payer_iban = 'FI8359986950002741'
    receiver_iban = 'FI4859986920215738'
    amount = 5

    payment = init_payment(payer_iban, receiver_iban, amount)
    payment_id = payment['paymentId']
    print("Created payment id {}".format(payment_id))

    confirmation = confirm_payment(payment_id)
    print('Account list after payment: {}'.format(get_accounts()))





if __name__ == '__main__':
    main()