import requests

from switcher_client.errors import RemoteAuthError
from switcher_client.context import Context

class Remote:

    @staticmethod
    def auth(context: Context):
        url = context.url + '/criteria/auth'

        response = Remote.do_post(url, {
            'domain': context.domain,
            'component': context.component,
            'environment': context.environment,
        }, {
            'switcher-api-key': context.api_key,
            'Content-Type': 'application/json',
        })
        
        if response.status_code == 200:
            return response.json()['token'], response.json()['exp']

        raise RemoteAuthError('Invalid API key')

    @staticmethod
    def do_post(url, data, headers) -> requests.Response:
        """ Perform a POST request """
        return requests.post(url, json=data, headers=headers)