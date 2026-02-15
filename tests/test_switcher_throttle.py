import time

from typing import Optional
from pytest_httpx import HTTPXMock

from switcher_client import Client
from switcher_client.lib.globals.global_context import ContextOptions

def test_throttle(httpx_mock):
    """ Should throttle remote API calls and use cached response """

    # given
    given_auth(httpx_mock)
    given_check_criteria(httpx_mock, show_details=True, response={'result': True})
    given_context()

    switcher = Client.get_switcher()
    switcher.throttle(1000)  # 1 second throttle

    # test
    response = switcher.is_on_with_details('MY_SWITCHER_THROTTLE')
    assert response.result is True
    assert response.metadata == {}

    # when - call again within throttle period (no new API call should be made, cached response should be used)
    response = switcher.is_on_with_details('MY_SWITCHER_THROTTLE')
    assert switcher.is_on('MY_SWITCHER_THROTTLE') is True
    assert response.result is True
    assert response.metadata == {'cached': True}

    time.sleep(1)

    # when - call again outside of throttle period (new API call should be made, cached response should be updated)
    given_check_criteria(httpx_mock, show_details=True, response={'result': False})
    response = switcher.is_on_with_details('MY_SWITCHER_THROTTLE')
    assert response.result is False
    assert response.metadata == {'cached': True}

# Helpers

def given_context(url='https://api.switcherapi.com', api_key='[API_KEY]'):
    Client.build_context(
        url=url,
        api_key=api_key,
        domain='Playground',
        component='switcher-playground',
        options=ContextOptions(throttle_max_workers=2)
    )

def given_auth(httpx_mock: HTTPXMock, status=200, token: Optional[str]='[token]', exp=int(round(time.time() * 1000))):
    httpx_mock.add_response(
        url='https://api.switcherapi.com/criteria/auth',
        method='POST',
        status_code=status,
        json={'token': token, 'exp': exp}
    )

def given_check_criteria(httpx_mock: HTTPXMock, status=200, key='MY_SWITCHER_THROTTLE', response={}, show_details=False, match=None):
    httpx_mock.add_response(
        is_reusable=False,
        url=f'https://api.switcherapi.com/criteria?showReason={str(show_details).lower()}&key={key}',
        method='POST',
        status_code=status,
        json=response,
        match_json=match
    )

