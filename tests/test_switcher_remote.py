import pytest
import responses
import time

from switcher_client.errors import RemoteAuthError
from switcher_client import Client, ContextOptions

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

def test_remote_err_no_key():
    """ Should raise an exception when no key is provided """

    # given
    given_context()

    switcher = Client.get_switcher()
    
    # test
    with pytest.raises(ValueError):
        switcher.is_on()

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

def given_auth(status=200, token='[token]', exp=int(round(time.time() * 1000))):
    responses.add(
        responses.POST,
        'https://api.switcherapi.com/criteria/auth',
        json={'token': token, 'exp': exp},
        status=status
    )

def given_check_criteria(status=200, key='MY_SWITCHER', response={}, show_details=False):
    responses.add(
        responses.POST,
        f'https://api.switcherapi.com/criteria?showReason={str(show_details).lower()}&key={key}',
        json=response,
        status=status
    )