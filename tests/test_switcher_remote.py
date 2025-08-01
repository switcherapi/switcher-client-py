from typing import Optional

import pytest
import responses
import time

from switcher_client.errors import RemoteAuthError
from switcher_client import Client
from switcher_client.lib.globals.global_auth import GlobalAuth

@responses.activate
def test_remote():
    """ Should call the remote API with success """

    # given
    given_auth()
    given_check_criteria(response={'result': True})
    given_context()

    switcher = Client.get_switcher()

    # test
    assert switcher.is_on('MY_SWITCHER')

@responses.activate
def test_remote_with_input():
    """ Should call the remote API with success using input parameters """

    # given
    given_auth()
    given_check_criteria(response={'result': True}, match=[
        responses.matchers.json_params_matcher({
            'entry': [{
                'strategy': 'VALUE_VALIDATION',
                'input': 'user_id'
            }]
        })
    ])
    given_context()

    switcher = Client.get_switcher()

    # test
    assert switcher \
        .check_value('user_id') \
        .is_on('MY_SWITCHER')

@responses.activate
def test_remote_with_prepare():
    """ Should prepare call the remote API with success """

    # given
    given_auth()
    given_check_criteria(response={'result': True}, match=[
        responses.matchers.json_params_matcher({
            'entry': [{
                'strategy': 'VALUE_VALIDATION',
                'input': 'user_id'
            }]
        })
    ])
    given_context()

    switcher = Client.get_switcher()

    # test
    switcher.check_value('user_id').prepare('MY_SWITCHER')
    assert switcher.is_on()
    
@responses.activate
def test_remote_with_details():
    """ Should call the remote API with success using detailed response """

    # given
    given_auth()
    given_check_criteria(
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

@responses.activate
def test_remote_renew_token():
    """ Should renew the token when it is expired """

    # given
    given_auth(status=200, token='[expired_token]', exp=int(round(time.time())) - 3600)
    given_auth(status=200, token='[new_token]', exp=int(round(time.time())) + 3600)
    given_check_criteria(response={'result': True})
    given_context()

    switcher = Client.get_switcher()

    # test
    switcher.is_on('MY_SWITCHER')
    assert GlobalAuth.get_token() == '[expired_token]'
    switcher.is_on('MY_SWITCHER')
    assert GlobalAuth.get_token() == '[new_token]'

@responses.activate
def test_remote_err_no_key():
    """ Should raise an exception when no key is provided """

    # given
    given_auth()
    given_context()

    switcher = Client.get_switcher()
    
    # test
    with pytest.raises(ValueError) as excinfo:
        switcher.is_on()

    assert 'Missing key field' in str(excinfo.value)

@responses.activate
def test_remote_err_no_token():
    """ Should raise an exception when no token is provided """

    # given
    given_auth(status=200, token=None)
    given_context()

    switcher = Client.get_switcher()

    # test
    with pytest.raises(ValueError) as excinfo:
        switcher.is_on('MY_SWITCHER')

    assert 'Missing token field' in str(excinfo.value)

@responses.activate
def test_remote_err_invalid_api_key():
    """ Should raise an exception when the API key is invalid """

    # given
    given_auth(status=401)
    given_context()

    switcher = Client.get_switcher()

    # test
    with pytest.raises(RemoteAuthError) as excinfo:
        switcher.is_on('MY_SWITCHER')

    assert 'Invalid API key' in str(excinfo.value)

@responses.activate
def test_remote_err_check_criteria():
    """ Should raise an exception when the check criteria fails """

    # given
    given_auth()
    given_check_criteria(status=500)
    given_context()

    switcher = Client.get_switcher()

    # test
    with pytest.raises(Exception) as excinfo:
        switcher.is_on('MY_SWITCHER')

    assert '[check_criteria] failed with status: 500' in str(excinfo.value)

# Helpers

def given_context(url='https://api.switcherapi.com', api_key='[API_KEY]'):
    Client.build_context(
        url=url,
        api_key=api_key,
        domain='Playground',
        component='switcher-playground'
    )

def given_auth(status=200, token: Optional[str]='[token]', exp=int(round(time.time() * 1000))):
    responses.add(
        responses.POST,
        'https://api.switcherapi.com/criteria/auth',
        json={'token': token, 'exp': exp},
        status=status
    )

def given_check_criteria(status=200, key='MY_SWITCHER', response={}, show_details=False, match=[]):
    responses.add(
        responses.POST,
        f'https://api.switcherapi.com/criteria?showReason={str(show_details).lower()}&key={key}',
        json=response,
        status=status,
        match=match
    )
