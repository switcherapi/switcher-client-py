import requests
from typing import Optional

from switcher_client.errors import RemoteAuthError
from switcher_client.errors import RemoteCriteriaError
from switcher_client.lib.globals.global_context import Context
from switcher_client.lib.types import ResultDetail

class Remote:

    @staticmethod
    def auth(context: Context):
        """ Authenticate """

        url = f'{context.url}/criteria/auth'
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
    def check_criteria(
        token: Optional[str], context: Context, 
        key: Optional[str], input: dict = {}, show_details = True) -> ResultDetail:
        """ Check criteria """

        url = f'{context.url}/criteria?showReason={str(show_details).lower()}&key={key}'
        response = Remote.do_post(url, input, Remote.get_header(token))
        
        if response.status_code == 200:
            json_response = response.json()
            return ResultDetail(
                result=json_response['result'],
                reason=json_response.get('reason', None)
            )

        raise RemoteCriteriaError(f'[check_criteria] failed with status: {response.status_code}')

    @staticmethod
    def do_post(url, data, headers) -> requests.Response:
        """ Perform a POST request """
        return requests.post(url, json=data, headers=headers)
    
    @staticmethod
    def get_header(token: Optional[str]):
        return {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
        }