from http_types import HttpExchange


class DataExtractor:
    def __init__(self):
        pass

    def extract_data(self, entity_locations, recordings: HttpExchange):
        return {'account': [{"id": 1, "iban": "F1111"}, {"id": 2, "iban": "F1112"}],
                'payment': [{"id": 1, "amount": 10}]}