import pytest
import time
import threading
import httpx

from unittest.mock import Mock, patch

from tests.helpers import (
    given_context,
    given_auth,
    given_check_criteria,
    given_check_criteria_exception,
    given_check_health_exception
)

from switcher_client import Client
from switcher_client.errors import RemoteAuthError, RemoteCriteriaError
from switcher_client.lib.globals.global_auth import GlobalAuth
from switcher_client.lib.globals.global_context import ContextOptions, RemoteOptions
from switcher_client.lib.remote import Remote

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

def test_remote_autorenew_token(httpx_mock):
    """ Should refresh the token before it expires in the background """

    # given
    given_auth(httpx_mock, status=200, token='[token_1]', exp=int(round(time.time())) + 2)
    given_auth(httpx_mock, status=200, token='[token_2]', exp=int(round(time.time())) + 3600)
    given_check_criteria(httpx_mock, response={'result': True})
    given_context(options=ContextOptions(
        remote=RemoteOptions(auto_renew_token=True)
    ))

    switcher = Client.get_switcher()

    # test
    switcher.is_on('MY_SWITCHER')
    assert GlobalAuth.get_token() == '[token_1]'
    time.sleep(3)  # Wait for the token to expire and auto-renew
    assert GlobalAuth.get_token() == '[token_2]'

def test_remote_autorenew_token_disabled(httpx_mock):
    """ Should not create a background renewer when auto renew is disabled """

    # given
    given_auth(httpx_mock, status=200, token='[token_1]', exp=int(round(time.time())) + 2)
    given_check_criteria(httpx_mock, response={'result': True})
    given_context(options=ContextOptions(
        remote=RemoteOptions(auto_renew_token=False)
    ))

    with patch('switcher_client.lib.remote_auth.threading.Timer') as mock_timer:
        switcher = Client.get_switcher()

        # test
        switcher.is_on('MY_SWITCHER')
        assert GlobalAuth.get_token() == '[token_1]'
        time.sleep(3)
        assert GlobalAuth.get_token() == '[token_1]'
        mock_timer.assert_not_called()

def test_remote_autorenew_token_failure(httpx_mock):
    """ Should stop auto renew after background failure and restart after foreground auth """

    # given
    real_timer = threading.Timer
    given_auth(httpx_mock, status=200, token='[token_1]', exp=int(round(time.time())) + 6)
    given_auth(httpx_mock, status=500, token=None, exp=int(round(time.time())) + 3600)
    given_auth(httpx_mock, status=200, token='[token_2]', exp=int(round(time.time())) + 13)
    given_auth(httpx_mock, status=200, token='[token_3]', exp=int(round(time.time())) + 3600)
    given_check_criteria(httpx_mock, response={'result': True})
    given_check_criteria(httpx_mock, response={'result': True})
    given_context(options=ContextOptions(
        remote=RemoteOptions(auto_renew_token=True)
    ))

    with patch('switcher_client.lib.remote_auth.threading.Timer',
        side_effect=lambda *args, **kwargs: real_timer(*args, **kwargs)) as mock_timer:
        switcher = Client.get_switcher()

        # test
        assert switcher.is_on('MY_SWITCHER')
        assert GlobalAuth.get_token() == '[token_1]'
        assert mock_timer.call_count == 1

        time.sleep(2)
        assert GlobalAuth.get_token() == '[token_1]'
        assert mock_timer.call_count == 1

        time.sleep(5)
        assert switcher.is_on('MY_SWITCHER')
        assert GlobalAuth.get_token() == '[token_2]'
        assert mock_timer.call_count == 2

        time.sleep(2)
        assert GlobalAuth.get_token() == '[token_3]'
        assert mock_timer.call_count == 3

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

def test_remote_with_custom_cert(httpx_mock):
    """ Should call the remote API with success using a custom certificate """

    # Reset Remote client to ensure fresh SSL context creation
    from switcher_client.lib.remote import Remote
    Remote._client = None

    # given
    given_auth(httpx_mock)
    given_check_criteria(httpx_mock, response={'result': True})
    given_context(options=ContextOptions(
        remote=RemoteOptions(cert_path='tests/fixtures/dummy_cert.pem')
    ))

    switcher = Client.get_switcher()

    # test
    mock_ssl_context = Mock()
    with patch('ssl.create_default_context', return_value=mock_ssl_context):
        assert switcher.is_on('MY_SWITCHER')
        mock_ssl_context.load_cert_chain.assert_called_once_with(
            certfile='tests/fixtures/dummy_cert.pem'
        )

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
    with pytest.raises(RemoteCriteriaError) as excinfo:
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

def test_remote_err_check_criteria_unavailable(httpx_mock):
    """ Should raise an exception when the remote criteria endpoint is unavailable """

    # given
    given_auth(httpx_mock)
    given_check_criteria_exception(httpx_mock, httpx.ConnectTimeout('timed out'), key='MY_SWITCHER')
    given_context()

    switcher = Client.get_switcher()

    # test
    with pytest.raises(RemoteCriteriaError) as excinfo:
        switcher.is_on('MY_SWITCHER')

    assert '[check_criteria] remote unavailable' in str(excinfo.value)

def test_remote_health_check_unavailable(httpx_mock):
    """ Should return false when the remote health endpoint is unavailable """

    # given
    given_check_health_exception(httpx_mock, httpx.ConnectError('connection failed'))
    given_context()

    # test
    assert not Remote.check_api_health(Client._context)

def test_remote_client_rebuilds_when_timeout_changes(httpx_mock):
    """ Should rebuild the shared remote client when timeout options change """

    # given
    Remote._client = None
    Remote._client_config = None
    given_auth(httpx_mock)
    given_check_criteria(httpx_mock, response={'result': True}, match={'entry': []},
        match_extensions={
            'timeout': {
                'connect': 0.3,
                'read': 5.0,
                'write': 5.0,
                'pool': 5.0
            }
        }
    )
    given_auth(httpx_mock)
    given_check_criteria(httpx_mock, response={'result': True}, match={'entry': []},
        match_extensions={
            'timeout': {
                'connect': 1.2,
                'read': 1.3,
                'write': 1.4,
                'pool': 1.5
            }
        }
    )

    given_context(options=ContextOptions(
        remote=RemoteOptions(
            connect_timeout=0.3,
            read_timeout=5.0,
            write_timeout=5.0,
            pool_timeout=5.0
        )
    ))
    assert Client.get_switcher().is_on('MY_SWITCHER')

    given_context(options=ContextOptions(
        remote=RemoteOptions(
            connect_timeout=1.2,
            read_timeout=1.3,
            write_timeout=1.4,
            pool_timeout=1.5
        )
    ))

    # test
    assert Client.get_switcher().is_on('MY_SWITCHER')

def test_remote_client_uses_default_connection_limits():
    """ Should build the shared remote client using the default connection limit options """

    # given
    Remote._client = None
    Remote._client_config = None
    given_context()

    # test
    client = Remote._get_client(Client._context)
    pool = client._transport._pool # type: ignore
    assert pool._max_keepalive_connections == 20
    assert pool._max_connections == 100
    assert pool._keepalive_expiry == 30.0

def test_remote_client_rebuilds_when_connection_limits_change():
    """ Should rebuild the shared remote client when connection limit options change """

    # given
    Remote._client = None
    Remote._client_config = None
    given_context(options=ContextOptions(
        remote=RemoteOptions(
            max_keepalive_connections=5,
            max_connections=10,
            keepalive_expiry=15.0
        )
    ))

    # test
    client = Remote._get_client(Client._context)
    pool = client._transport._pool # type: ignore
    assert pool._max_keepalive_connections == 5
    assert pool._max_connections == 10
    assert pool._keepalive_expiry == 15.0

    given_context(options=ContextOptions(
        remote=RemoteOptions(
            max_keepalive_connections=8,
            max_connections=16,
            keepalive_expiry=25.0
        )
    ))

    rebuilt_client = Remote._get_client(Client._context)
    assert rebuilt_client is not client
    rebuilt_pool = rebuilt_client._transport._pool # type: ignore
    assert rebuilt_pool._max_keepalive_connections == 8
    assert rebuilt_pool._max_connections == 16
    assert rebuilt_pool._keepalive_expiry == 25.0
