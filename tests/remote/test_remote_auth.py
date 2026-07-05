import threading

from unittest.mock import Mock, patch

from tests.helpers import given_context

from switcher_client.lib.globals.global_auth import GlobalAuth
from switcher_client.lib.globals.global_context import ContextOptions, RemoteOptions
from switcher_client.lib.remote_auth import RemoteAuth

def test_refresh_token_skips_auth_for_stale_generation():
    """ Should ignore stale background refresh attempts before calling remote auth """

    # given
    given_context(options=ContextOptions(
        remote=RemoteOptions(auto_renew_token=True)
    ))
    GlobalAuth.set_token('[current_token]')
    GlobalAuth.set_exp('9999999999')

    # test
    with patch('switcher_client.lib.remote_auth.Remote.auth') as mock_auth:
        RemoteAuth._refresh_token(generation=_stale_generation())

    assert GlobalAuth.get_token() == '[current_token]'
    mock_auth.assert_not_called()

def test_refresh_token_discards_stale_result_after_auth_returns():
    """ Should discard auth results when the renewer becomes stale during the request """

    # given
    given_context(options=ContextOptions(
        remote=RemoteOptions(auto_renew_token=True)
    ))
    GlobalAuth.set_token('[current_token]')
    GlobalAuth.set_exp('9999999999')

    auth_started = threading.Event()
    release_auth = threading.Event()
    current_generation = _current_generation()

    def fake_auth(_):
        auth_started.set()
        release_auth.wait(timeout=2)
        return '[new_token]', '9999999999'

    with patch('switcher_client.lib.remote_auth.Remote.auth', side_effect=fake_auth) as mock_auth, \
        patch.object(RemoteAuth, '_schedule_auto_renew') as mock_schedule:
        refresh_thread = threading.Thread(
            target=RemoteAuth._refresh_token,
            kwargs={'generation': current_generation}
        )
        refresh_thread.start()

        assert auth_started.wait(timeout=1)
        RemoteAuth._stop_auto_renew()
        release_auth.set()
        refresh_thread.join(timeout=2)

    assert not refresh_thread.is_alive()
    assert GlobalAuth.get_token() == '[current_token]'
    assert mock_auth.call_count == 1
    mock_schedule.assert_not_called()

def test_stop_auto_renew_ignores_stale_generation():
    """ Should not cancel the active renewer when stop is requested with a stale generation """

    # given
    given_context(options=ContextOptions(
        remote=RemoteOptions(auto_renew_token=True)
    ))
    active_timer = Mock()
    current_generation = _current_generation()
    RemoteAuth._RemoteAuth__auto_renew_timer = active_timer  # type: ignore

    # test
    RemoteAuth._stop_auto_renew(generation=_stale_generation())

    assert _current_generation() == current_generation
    assert RemoteAuth._RemoteAuth__auto_renew_timer is active_timer  # type: ignore
    active_timer.cancel.assert_not_called()

# Helpers

def _current_generation() -> int:
    return RemoteAuth._RemoteAuth__auto_renew_generation # type: ignore

def _stale_generation() -> int:
    current_generation = _current_generation()
    return current_generation - 1 if current_generation > 0 else current_generation + 1
