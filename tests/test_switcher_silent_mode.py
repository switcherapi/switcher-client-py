import time

from typing import Optional
from pytest_httpx import HTTPXMock

from switcher_client import Client
from switcher_client.lib.globals.global_context import ContextOptions

def test_silent_mode_for_check_criteria(httpx_mock):
    """ Should use the silent mode when the remote API is not available for check criteria """

    # given
    given_auth(httpx_mock)
    given_check_criteria(httpx_mock, key='FF2FOR2022', response={'error': 'Too many requests'}, status=429)
    given_check_health(httpx_mock, status=500)
    given_context(silent_mode='1s')

    switcher = Client.get_switcher('FF2FOR2022')

    # test
    # assert silent mode being used while registering the error
    assert switcher.is_on('FF2FOR2022')

    # assert silent mode being used in the next call
    time.sleep(1.5)
    assert switcher.is_on('FF2FOR2022')

def test_silent_mode_for_check_criteria_restabilished(httpx_mock):
    """ Should retry check criteria once the remote API is restabilished and the token is renewed """

    # given
    given_auth(httpx_mock)
    given_check_criteria(httpx_mock, key='FF2FOR2022', response={'error': 'Too many requests'}, status=429)
    given_context(silent_mode='1s')

    switcher = Client.get_switcher('FF2FOR2022')

    # test
    # assert silent mode being used while registering the error
    assert switcher.is_on('FF2FOR2022')

    # assert from remote API once the API is restabilished and the token is renewed
    given_check_criteria(httpx_mock, key='FF2FOR2022', response={'result': True}, status=200)
    given_check_health(httpx_mock, status=200)
    time.sleep(1.5)
    assert switcher.is_on('FF2FOR2022')

# Helpers

def given_context(silent_mode: Optional[str] = '5m'):
    Client.build_context(
        url='https://api.switcherapi.com',
        api_key='[API_KEY]',
        domain='Playground',
        component='switcher-playground',
        options=ContextOptions(
            silent_mode=silent_mode,
            snapshot_location='tests/snapshots',
        )
    )

def given_auth(httpx_mock: HTTPXMock, status=200, token: Optional[str]='[token]', exp=int(round(time.time() * 1000))):
    httpx_mock.add_response(
        is_reusable=True,
        url='https://api.switcherapi.com/criteria/auth',
        method='POST',
        status_code=status,
        json={'token': token, 'exp': exp}
    )

def given_check_criteria(httpx_mock: HTTPXMock, status=200, key='MY_SWITCHER', response={}, show_details=False, match=None):
    httpx_mock.add_response(
        is_reusable=False,
        url=f'https://api.switcherapi.com/criteria?showReason={str(show_details).lower()}&key={key}',
        method='POST',
        status_code=status,
        json=response,
        match_json=match
    )

def given_check_health(httpx_mock: HTTPXMock, status=200):
    httpx_mock.add_response(
        is_reusable=False,
        url='https://api.switcherapi.com/check',
        method='GET',
        status_code=status,
    )

