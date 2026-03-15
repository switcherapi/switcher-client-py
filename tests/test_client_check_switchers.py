import time

from typing import Optional
from pytest_httpx import HTTPXMock

from switcher_client.client import Client
from switcher_client.errors import LocalSwitcherError, RemoteSwitcherError
from switcher_client.lib.globals.global_context import ContextOptions

def test_check_remote_switchers(httpx_mock):
    """ Should check remote switchers with success """

    # given
    given_auth(httpx_mock)
    given_check_switchers(httpx_mock)
    given_context()

    # test
    Client.check_switchers(['MY_SWITCHER', 'ANOTHER_SWITCHER'])

def test_check_remote_switchers_not_found(httpx_mock):
    """ Should check remote switchers and raise RemoteSwitcherError with not found switchers """

    # given
    given_auth(httpx_mock)
    given_check_switchers(httpx_mock, not_found=['MY_SWITCHER'])
    given_context()

    # test
    try:
        Client.check_switchers(['MY_SWITCHER', 'ANOTHER_SWITCHER'])
        assert False, 'Expected RemoteSwitcherError to be raised'
    except RemoteSwitcherError as e:
        assert str(e) == 'MY_SWITCHER not found'

def test_check_remote_switchers_api_error(httpx_mock):
    """ Should check remote switchers and raise RemoteError when API returns an error """

    # given
    given_auth(httpx_mock)
    given_check_switchers(httpx_mock, status=500)
    given_context()

    # test
    try:
        Client.check_switchers(['MY_SWITCHER', 'ANOTHER_SWITCHER'])
        assert False, 'Expected RemoteError to be raised'
    except Exception as e:
        assert str(e) == '[check_switchers] failed with status: 500'

def test_chek_remote_switchers_auth_error(httpx_mock):
    """ Should check remote switchers and raise RemoteError when API returns an auth error """

    # given
    given_auth(httpx_mock, status=401)
    given_context()

    # test
    try:
        Client.check_switchers(['MY_SWITCHER', 'ANOTHER_SWITCHER'])
        assert False, 'Expected RemoteError to be raised'
    except Exception as e:
        assert str(e) == 'Invalid API key'

def test_check_local_switchers():
    """ Should check local switchers with success """

    # given
    given_context(options=ContextOptions(snapshot_location='tests/snapshots', local=True))
    snapshot_version = Client.load_snapshot()

    # test
    assert snapshot_version == 1
    Client.check_switchers(['FF2FOR2020', 'FF2FOR2021'])

def test_check_local_switchers_not_found():
    """ Should check local switchers and raise LocalSwitcherError with not found switchers """

    # given
    given_context(options=ContextOptions(snapshot_location='tests/snapshots', local=True))
    snapshot_version = Client.load_snapshot()

    # test
    assert snapshot_version == 1
    try:
        Client.check_switchers(['FF2FOR2020', 'NON_EXISTENT_SWITCHER'])
        assert False, 'Expected LocalSwitcherError to be raised'
    except LocalSwitcherError as e:
        assert str(e) == 'NON_EXISTENT_SWITCHER not found'

def test_check_local_switchers_no_snapshot():
    """ Should check local switchers and raise LocalSwitcherError when no snapshot is loaded """

    # given
    given_context(options=ContextOptions(local=True))

    # test
    try:
        Client.check_switchers(['FF2FOR2020', 'NON_EXISTENT_SWITCHER'])
        assert False, 'Expected LocalSwitcherError to be raised'
    except LocalSwitcherError as e:
        assert str(e) == 'FF2FOR2020, NON_EXISTENT_SWITCHER not found'

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

def given_check_switchers(httpx_mock: HTTPXMock, status=200, not_found: Optional[list[str]]=None):
    httpx_mock.add_response(
        url='https://api.switcherapi.com/criteria/switchers_check',
        method='POST',
        status_code=status,
        json={'not_found': not_found or []}
    )