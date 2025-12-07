import pytest
import time

from typing import Optional
from pytest_httpx import HTTPXMock

from switcher_client.errors import RemoteAuthError
from switcher_client import Client
from switcher_client.lib.globals.global_auth import GlobalAuth

def test_throttle(httpx_mock):
    """ TODO Should throttle remote API calls and use cached response """

    # given
    given_auth(httpx_mock)
    given_check_criteria(httpx_mock, show_details=True, response={'result': True})
    given_context()

    switcher = Client.get_switcher()
    switcher.throttle(1000)  # 1 second throttle

    # test
    response = switcher.is_on_with_details('MY_SWITCHER')
    assert response.result is True
    assert response.metadata == {}

    # when - call again within throttle period
    # response = switcher.is_on_with_details('MY_SWITCHER')
    # assert response.result is True
    # assert response.metadata == {'cached': True}

# Helpers

def given_context(url='https://api.switcherapi.com', api_key='[API_KEY]'):
    Client.build_context(
        url=url,
        api_key=api_key,
        domain='Playground',
        component='switcher-playground'
    )

def given_auth(httpx_mock: HTTPXMock, status=200, token: Optional[str]='[token]', exp=int(round(time.time() * 1000))):
    httpx_mock.add_response(
        url='https://api.switcherapi.com/criteria/auth',
        method='POST',
        status_code=status,
        json={'token': token, 'exp': exp}
    )

def given_check_criteria(httpx_mock: HTTPXMock, status=200, key='MY_SWITCHER', response={}, show_details=False, match=None):
    httpx_mock.add_response(
        is_reusable=True,
        url=f'https://api.switcherapi.com/criteria?showReason={str(show_details).lower()}&key={key}',
        method='POST',
        status_code=status,
        json=response,
        match_json=match
    )

