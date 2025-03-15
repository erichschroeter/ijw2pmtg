import logging
import requests

class Scryfall:
    def __init__(self, server_url='https://api.scryfall.com'):
        self.server_url = server_url

    def cards_named(self, card_name, **kwargs):
        return self._endpoint_get('cards/named', fuzzy=card_name, **kwargs)

    def cards_image(self, uuid, format='image', version='png', **kwargs):
        return self._endpoint_get(f'cards/{uuid}', format=format, version=version, **kwargs)

    def cards_search(self, query, format='json'):
        return self._endpoint_get(f'cards/search', format=format, q=query)

    def _endpoint_get(self, endpoint, **kwargs):
        url = f'{self.server_url}/{endpoint}'
        logging.debug(f'GET {url} with params {kwargs}')
        response = requests.get(url, params=kwargs)
        logging.debug(f'RESPONSE {response}')
        response.raise_for_status()
        return response
