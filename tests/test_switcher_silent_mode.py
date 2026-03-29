import time

from tests.helpers import given_context, given_auth, given_check_criteria, given_check_health

from switcher_client import Client
from switcher_client.lib.globals.global_context import ContextOptions

async_error = None
context_options = ContextOptions(silent_mode='5m', snapshot_location='tests/snapshots')

def test_silent_mode_for_check_criteria(httpx_mock):
    """ Should use the silent mode when the remote API is not available for check criteria """

    options = ContextOptions(**vars(context_options))
    options.silent_mode = '1s'

    # given
    given_auth(httpx_mock)
    given_check_criteria(httpx_mock, key='FF2FOR2022', response={'error': 'Too many requests'}, status=429)
    given_check_health(httpx_mock, status=500)
    given_context(options=options)

    Client.subscribe_notify_error(lambda error: globals().update(async_error=str(error)))
    switcher = Client.get_switcher('FF2FOR2022')

    # test
    # assert silent mode being used while registering the error
    assert switcher.is_on('FF2FOR2022')
    assert async_error == '[check_criteria] failed with status: 429'

    # assert silent mode being used in the next call
    time.sleep(1.5)
    globals().update(async_error=None)
    assert switcher.is_on('FF2FOR2022')
    assert async_error is None

def test_silent_mode_for_check_criteria_restabilished(httpx_mock):
    """ Should retry check criteria once the remote API is restabilished and the token is renewed """

    options = ContextOptions(**vars(context_options))
    options.silent_mode = '1s'

    # given
    given_auth(httpx_mock, is_reusable=True)
    given_check_criteria(httpx_mock, key='FF2FOR2022', response={'error': 'Too many requests'}, status=429)
    given_context(options=options)

    Client.subscribe_notify_error(lambda error: globals().update(async_error=str(error)))
    switcher = Client.get_switcher('FF2FOR2022')

    # test
    # assert silent mode being used while registering the error
    assert switcher.is_on('FF2FOR2022')
    assert async_error == '[check_criteria] failed with status: 429'

    # assert from remote API once the API is restabilished and the token is renewed
    given_check_criteria(httpx_mock, key='FF2FOR2022', response={'result': True}, status=200)
    given_check_health(httpx_mock, status=200)

    time.sleep(1.5)
    globals().update(async_error=None)
    assert switcher.is_on('FF2FOR2022')
    assert async_error is None
