import requests


def main():
    api = 'https://sandbox.apis.op-palvelut.fi/'

    account_headers = {
        'x-api-key': 'ZoStul8nNuwq1SYCzSrLcO1wAj4Tyf7x',
        'x-request-id': "12345",
        'x-session-id': "12345",
        'authorization': "Bearer 6c18c234b1b18b1d97c7043e2e41135c293d0da9",
        'x-authorization': "6c18c234b1b18b1d97c7043e2e41135c293d0da9",
    }
    #
    payments_headers = {
        'x-api-key': 'ZoStul8nNuwq1SYCzSrLcO1wAj4Tyf7x',
        'x-request-id': "12345",
        'x-session-id': "12345",
        # 'authorization': "Bearer 6c18c234b1b18b1d97c7043e2e41135c293d0da9",
        'x-authorization': "6c18c234b1b18b1d97c7043e2e41135c293d0da9",
    }

    url = api + '/accounts/v3/accounts'
    response = requests.get(url, headers=account_headers)

    print('Account list: ')
    print(response)

    payer_iban = 'FI8359986950002741'
    receiver_iban = 'FI4859986920215738'
    amount = 5
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

    url = api + '/v1/payments/initiate'
    response = requests.post(url, headers=payments_headers, json=body)
    print(response.status_code)
    print(response.json())

    payment = response.json()
    payment_id = payment['paymentId']
    print(payment_id)

    body = {
            'paymentId': payment_id
        }
    url = api + '/v1/payments/confirm'
    response = requests.post(url, headers=payments_headers, json=body)
    print(response.status_code)
    print(response.json())


if __name__ == '__main__':
    main()