import json
import os
import pytest
import time

from typing import Optional
from pytest_httpx import HTTPXMock

from switcher_client import Client
from switcher_client.errors import RemoteError
from switcher_client.lib.globals.global_context import DEFAULT_ENVIRONMENT, ContextOptions
from switcher_client.lib.globals.global_snapshot import LoadSnapshotOptions

def test_load_from_snapshot_in_memory(httpx_mock):
    """ Should load in-memory Domain from snapshot remote """

    # given
    given_auth(httpx_mock)
    given_check_snapshot_version(httpx_mock, version=0, status=False)
    given_resolve_snapshot(httpx_mock, data=load_snapshot_fixture('tests/snapshots/default_load_1.json'))
    given_context(environment='default_load_1')

    # test
    version = Client.load_snapshot(LoadSnapshotOptions(
        fetch_remote=True
    ))

    assert Client.snapshot_version() == 1588557288040
    assert version == Client.snapshot_version()

def test_load_from_snapshot_no_update(httpx_mock):
    """ Should not update snapshot if version is the same """

    # given
    given_auth(httpx_mock)
    given_check_snapshot_version(httpx_mock, version=1588557288040, status=True)
    given_context(snapshot_location='tests/snapshots', environment='default_load_1')

    # test
    version = Client.load_snapshot() # load from file
    updated = Client.check_snapshot() # check for updates

    assert Client.snapshot_version() == 1588557288040
    assert version == Client.snapshot_version()
    assert not updated

def test_check_snapshot_version_error(httpx_mock):
    """ Should handle errors when checking snapshot version """

    # given
    given_auth(httpx_mock)
    given_check_snapshot_version(httpx_mock, status_code=500, version=1588557288040)
    given_context(snapshot_location='tests/snapshots', environment='default_load_1')

    Client.load_snapshot() # load from file

    # test
    with pytest.raises(RemoteError) as excinfo:
        Client.check_snapshot()

    assert '[check_snapshot_version] failed with status: 500' in str(excinfo.value)

def test_resolve_snapshot_error(httpx_mock):
    """ Should handle errors when resolving snapshot """

    # given
    given_auth(httpx_mock)
    given_check_snapshot_version(httpx_mock, version=1588557288040, status=False)
    given_resolve_snapshot(httpx_mock, status_code=500)
    given_context(snapshot_location='tests/snapshots', environment='default_load_1')

    Client.load_snapshot() # load from file

    # test
    with pytest.raises(RemoteError) as excinfo:
        Client.check_snapshot()

    assert '[resolve_snapshot] failed with status: 500' in str(excinfo.value)

def test_auto_update_snapshot_from_context(httpx_mock):
    """ Should auto-update snapshot every second from context """

    # given - load initial snapshot
    given_auth(httpx_mock)
    given_check_snapshot_version(httpx_mock, version=0, status=False)
    given_resolve_snapshot(httpx_mock, data=load_snapshot_fixture('tests/snapshots/default_load_1.json'))

    # given - snapshot out-of-date, needs update
    given_check_snapshot_version(httpx_mock, version=1588557288040, status=False) # needs update
    given_resolve_snapshot(httpx_mock, data=load_snapshot_fixture('tests/snapshots/default_load_2.json'))

    # given - context
    given_context(
        snapshot_location='tests/snapshots/temp', 
        environment='generated-auto-update',
        snapshot_auto_update_interval=1
    )

    # test
    Client.load_snapshot(LoadSnapshotOptions(fetch_remote=True))
    assert Client.snapshot_version() == 1588557288040
    
    time.sleep(1.5) # wait for auto-update to trigger
    assert Client.snapshot_version() == 1588557288041

    # tear down
    Client.terminate_snapshot_auto_update()
    delete_snapshot_file('./tests/snapshots/temp', 'generated-auto-update')

def test_auto_update_snapshot(httpx_mock):
    """ Should auto-update snapshot every second """

    # given - load initial snapshot
    given_auth(httpx_mock)
    given_check_snapshot_version(httpx_mock, version=0, status=False)
    given_resolve_snapshot(httpx_mock, data=load_snapshot_fixture('tests/snapshots/default_load_1.json'))

    # given - snapshot out-of-date, needs update
    given_check_snapshot_version(httpx_mock, version=1588557288040, status=False) # needs update
    given_resolve_snapshot(httpx_mock, data=load_snapshot_fixture('tests/snapshots/default_load_2.json'))

    # given - context
    given_context(
        snapshot_location='tests/snapshots/temp', 
        environment='generated-auto-update'
    )
    
    Client.load_snapshot(LoadSnapshotOptions(fetch_remote=True))

    # test
    callback_args = []
    Client.schedule_snapshot_auto_update(interval=1,
        callback=lambda error, updated: callback_args.append((error, updated))
    )

    time.sleep(1.5) # wait for auto-update to trigger

    error, updated = callback_args[0]
    assert error is None
    assert updated

    # tear down
    Client.terminate_snapshot_auto_update()
    delete_snapshot_file('./tests/snapshots/temp', 'generated-auto-update')

def test_not_auto_update_snapshot_when_error(httpx_mock):
    """ Should not auto-update snapshot if there is an error """

    # given - load initial snapshot
    given_auth(httpx_mock)
    given_check_snapshot_version(httpx_mock, version=0, status=False)
    given_resolve_snapshot(httpx_mock, data=load_snapshot_fixture('tests/snapshots/default_load_1.json'))

    # given - snapshot out-of-date, needs update
    given_check_snapshot_version(httpx_mock, version=1588557288040, status=False) # needs update
    given_resolve_snapshot(httpx_mock, status_code=500) # will cause error

    # given - context
    given_context(
        snapshot_location='tests/snapshots/temp', 
        environment='generated-auto-update-error'
    )
    
    Client.load_snapshot(LoadSnapshotOptions(fetch_remote=True))

    # test
    callback_args = []
    Client.schedule_snapshot_auto_update(interval=1,
        callback=lambda error, updated: callback_args.append((error, updated))
    )

    time.sleep(1.5) # wait for auto-update to trigger

    error, updated = callback_args[0]
    assert isinstance(error, RemoteError)
    assert '[resolve_snapshot] failed with status: 500' in str(error)
    assert not updated

    # tear down
    Client.terminate_snapshot_auto_update()
    delete_snapshot_file('./tests/snapshots/temp', 'generated-auto-update-error')

# Helpers

def given_auth(httpx_mock: HTTPXMock, status=200, token: Optional[str]='[token]', exp=int(round(time.time() * 1000)), is_reusable=False):
    httpx_mock.add_response(
        url='https://api.switcherapi.com/criteria/auth',
        method='POST',
        status_code=status,
        json={'token': token, 'exp': exp},
        is_reusable=is_reusable
    )

def given_check_snapshot_version(httpx_mock: HTTPXMock, status_code=200, version=0, status=False, is_reusable=False):
    httpx_mock.add_response(
        url=f'https://api.switcherapi.com/criteria/snapshot_check/{version}',
        method='GET',
        status_code=status_code,
        json={'status': status},
        is_reusable=is_reusable
    )

def given_resolve_snapshot(httpx_mock: HTTPXMock, status_code=200, data=[], is_reusable=False):
    httpx_mock.add_response(
        url='https://api.switcherapi.com/graphql',
        method='POST',
        status_code=status_code,
        json={'data': { 'domain': data}},
        is_reusable=is_reusable
    )

def given_context(url='https://api.switcherapi.com', 
                  api_key='[API_KEY]', 
                  environment=DEFAULT_ENVIRONMENT,
                  snapshot_location=None,
                  snapshot_auto_update_interval=None):
    Client.build_context(
        url=url,
        api_key=api_key,
        domain='Switcher API',
        component='switcher-client-python',
        environment=environment,
        options=ContextOptions(
            local=True,
            snapshot_location=snapshot_location,
            snapshot_auto_update_interval=snapshot_auto_update_interval
        )
    )

def load_snapshot_fixture(file_path: str):
    with open(file_path, 'r') as f:
        return json.loads(f.read()).get('domain', {})
    
def delete_snapshot_file(snapshot_location: str, environment: str):
    snapshot_file = f"{snapshot_location}/{environment}.json"
    if os.path.exists(snapshot_file):
        os.remove(snapshot_file)