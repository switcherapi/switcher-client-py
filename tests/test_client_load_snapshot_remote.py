import json
import pytest
import responses
import time
from typing import Optional

from switcher_client import Client
from switcher_client.errors import RemoteError
from switcher_client.lib.globals.global_context import DEFAULT_ENVIRONMENT, ContextOptions
from switcher_client.lib.globals.global_snapshot import LoadSnapshotOptions

@responses.activate
def test_load_from_snapshot_in_memory():
    """ Should load in-memory Domain from snapshot remote """

    # given
    given_auth()
    given_check_snapshot_version(version=0, status=False)
    given_resolve_snapshot(data=load_snapshot_fixture('tests/snapshots/default_load_1.json'))
    given_context(environment='default_load_1')

    # test
    version = Client.load_snapshot(LoadSnapshotOptions(
        fetch_remote=True
    ))

    assert Client.snapshot_version() == 1588557288040
    assert version == Client.snapshot_version()

@responses.activate
def test_load_from_snapshot_no_update():
    """ Should not update snapshot if version is the same """

    # given
    given_auth()
    given_check_snapshot_version(version=1588557288040, status=True)
    given_context(snapshot_location='tests/snapshots', environment='default_load_1')

    # test
    version = Client.load_snapshot() # load from file
    updated = Client.check_snapshot() # check for updates

    assert Client.snapshot_version() == 1588557288040
    assert version == Client.snapshot_version()
    assert not updated

@responses.activate
def test_check_snapshot_version_error():
    """ Should handle errors when checking snapshot version """

    # given
    given_auth()
    given_check_snapshot_version(status_code=500, version=1588557288040)
    given_context(snapshot_location='tests/snapshots', environment='default_load_1')

    Client.load_snapshot() # load from file

    # test
    with pytest.raises(RemoteError) as excinfo:
        Client.check_snapshot()

    assert '[check_snapshot_version] failed with status: 500' in str(excinfo.value)

@responses.activate
def test_resolve_snapshot_error():
    """ Should handle errors when resolving snapshot """

    # given
    given_auth()
    given_check_snapshot_version(version=1588557288040, status=False)
    given_resolve_snapshot(status_code=500)
    given_context(snapshot_location='tests/snapshots', environment='default_load_1')

    Client.load_snapshot() # load from file

    # test
    with pytest.raises(RemoteError) as excinfo:
        Client.check_snapshot()

    assert '[resolve_snapshot] failed with status: 500' in str(excinfo.value)

# Helpers

def given_auth(status=200, token: Optional[str]='[token]', exp=int(round(time.time() * 1000))):
    responses.add(
        responses.POST,
        'https://api.switcherapi.com/criteria/auth',
        json={'token': token, 'exp': exp},
        status=status
    )

def given_check_snapshot_version(status_code=200, version=0, status=False):
    responses.add(
        responses.GET,
        f'https://api.switcherapi.com/criteria/snapshot_check/{version}',
        json={'status': status},
        status=status_code
    )

def given_resolve_snapshot(status_code=200, data=[]):
    responses.add(
        responses.POST,
        'https://api.switcherapi.com/graphql',
        json={'data': data},
        status=status_code
    )

def given_context(url='https://api.switcherapi.com', 
                  api_key='[API_KEY]', 
                  environment=DEFAULT_ENVIRONMENT,
                  snapshot_location=None):
    Client.build_context(
        url=url,
        api_key=api_key,
        domain='Switcher API',
        component='switcher4deno',
        environment=environment,
        options=ContextOptions(
            local=True,
            snapshot_location=snapshot_location
        )
    )

def load_snapshot_fixture(file_path: str):
    with open(file_path, 'r') as f:
        return json.loads(f.read()).get('data', {})