import pytest
import time

from typing import Optional
from pytest_httpx import HTTPXMock

from switcher_client.errors import RemoteAuthError
from switcher_client import Client
from switcher_client.lib.globals.global_auth import GlobalAuth
from switcher_client.lib.globals.global_context import ContextOptions

async_error = None

def test_remote(httpx_mock):
    """ Should call the remote API with success """

    # given
    given_auth(httpx_mock)
    given_check_criteria(httpx_mock, response={'result': True})
    given_context()

    switcher = Client.get_switcher()

    # test
    assert switcher.is_on('MY_SWITCHER')

def test_remote_with_input(httpx_mock):
    """ Should call the remote API with success using input parameters """

    # given
    given_auth(httpx_mock)
    given_check_criteria(httpx_mock, response={'result': True}, match={
        'entry': [{
            'strategy': 'VALUE_VALIDATION',
            'input': 'user_id'
        }]
    })
    given_context()

    switcher = Client.get_switcher()

    # test
    assert switcher \
        .check_value('user_id') \
        .is_on('MY_SWITCHER')

def test_remote_with_prepare(httpx_mock):
    """ Should prepare call the remote API with success """

    # given
    given_auth(httpx_mock)
    given_check_criteria(httpx_mock, response={'result': True}, match={
        'entry': [{
            'strategy': 'VALUE_VALIDATION',
            'input': 'user_id'
        }]
    })
    given_context()

    switcher = Client.get_switcher()

    # test
    switcher.check_value('user_id').prepare('MY_SWITCHER')
    assert switcher.is_on()
    
def test_remote_with_details(httpx_mock):
    """ Should call the remote API with success using detailed response """

    # given
    given_auth(httpx_mock)
    given_check_criteria(
        httpx_mock,
        response={
            'result': True,
            'reason': 'Success',
            'metadata': {'key': 'value'}
        },
        show_details=True)
    given_context()

    switcher = Client.get_switcher()

    # test
    response = switcher.is_on_with_details('MY_SWITCHER')
    assert response
    assert response.reason == 'Success'
    assert response.result is True
    assert response.metadata == {'key': 'value'}
    assert isinstance(response.to_dict(), dict)

def test_remote_renew_token(httpx_mock):
    """ Should renew the token when it is expired """

    # given
    given_auth(httpx_mock, status=200, token='[expired_token]', exp=int(round(time.time())) - 3600)
    given_auth(httpx_mock, status=200, token='[new_token]', exp=int(round(time.time())) + 3600)
    given_check_criteria(httpx_mock, response={'result': True})
    given_context()

    switcher = Client.get_switcher()

    # test
    switcher.is_on('MY_SWITCHER')
    assert GlobalAuth.get_token() == '[expired_token]'
    switcher.is_on('MY_SWITCHER')
    assert GlobalAuth.get_token() == '[new_token]'

def test_remote_with_remote_required_request(httpx_mock):
    """ Should call the remote API with success for required remote request"""

    # given
    key = 'FF2FOR2022'
    given_auth(httpx_mock)
    given_check_criteria(httpx_mock, key=key, response={'result': True})
    given_context(options=ContextOptions(local=True, snapshot_location='tests/snapshots'))
    Client.load_snapshot()

    switcher = Client.get_switcher()

    # test
    assert switcher.remote().is_on(key)

def test_remote_err_with_remote_reqquired_request_no_local():
    """ Should raise an exception when local mode is not enabled and remote is forced """

    # given
    given_context(options=ContextOptions(local=False))

    switcher = Client.get_switcher()

    # test
    with pytest.raises(ValueError) as excinfo:
        switcher.remote().is_on('MY_SWITCHER')

    assert 'Local mode is not enabled' in str(excinfo.value)

def test_remote_err_no_key(httpx_mock):
    """ Should raise an exception when no key is provided """

    # given
    given_auth(httpx_mock)
    given_context()

    switcher = Client.get_switcher()
    
    # test
    with pytest.raises(ValueError) as excinfo:
        switcher.is_on()

    assert 'Missing key field' in str(excinfo.value)

def test_remote_err_no_token(httpx_mock):
    """ Should raise an exception when no token is provided """

    # given
    given_auth(httpx_mock, status=200, token=None)
    given_context()

    switcher = Client.get_switcher()

    # test
    with pytest.raises(ValueError) as excinfo:
        switcher.is_on('MY_SWITCHER')

    assert 'Missing token field' in str(excinfo.value)

def test_remote_err_invalid_api_key(httpx_mock):
    """ Should raise an exception when the API key is invalid """

    # given
    given_auth(httpx_mock, status=401)
    given_context()

    switcher = Client.get_switcher()

    # test
    with pytest.raises(RemoteAuthError) as excinfo:
        switcher.is_on('MY_SWITCHER')

    assert 'Invalid API key' in str(excinfo.value)


def test_remote_err_check_criteria(httpx_mock):
    """ Should raise an exception when the check criteria fails """

    # given
    given_auth(httpx_mock)
    given_check_criteria(httpx_mock, status=500)
    given_context()

    switcher = Client.get_switcher()

    # test
    with pytest.raises(Exception) as excinfo:
        switcher.is_on('MY_SWITCHER')

    assert '[check_criteria] failed with status: 500' in str(excinfo.value)

def test_remote_err_check_criteria_default_result(httpx_mock):
    """ Should return the default result when the check criteria fails """

    # given
    given_auth(httpx_mock)
    given_check_criteria(httpx_mock, show_details=True, status=500)
    given_context()

    globals().update(async_error=None)
    Client.subscribe_notify_error(lambda error: globals().update(async_error=str(error)))
    switcher = Client.get_switcher()

    # test
    feature = switcher.default_result(True).is_on_with_details('MY_SWITCHER')
    assert feature.result is True
    assert feature.reason == 'Default result'
    assert async_error == '[check_criteria] failed with status: 500'

# Helpers

def given_context(url='https://api.switcherapi.com', api_key='[API_KEY]', options = ContextOptions()):
    Client.build_context(
        url=url,
        api_key=api_key,
        domain='Playground',
        component='switcher-playground',
        options=options
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

