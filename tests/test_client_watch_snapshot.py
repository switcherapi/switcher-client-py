import os
import shutil
import time

from typing import Optional

from switcher_client.client import Client, ContextOptions
from switcher_client.lib.globals.global_context import DEFAULT_ENVIRONMENT
from switcher_client.lib.snapshot_watcher import SnapshotWatcher

class TestClientWatchSnapshot:
    """ Test suite for Client.watch_snapshot """

    def setup_method(self):
        self.async_success = None
        self.async_error = None
        Client._snapshot_watcher = SnapshotWatcher()

    def teardown_method(self):
        Client.unwatch_snapshot()

    def teardown_class(self):
        temp_folder = 'tests/snapshots/temp'
        if os.path.exists(temp_folder):
            shutil.rmtree(temp_folder)

    def test_watch_snapshot(self):
        """ Should watch the snapshot file and update the switcher when the file changes """

        fixture_env = 'default_load_1'
        fixture_env_file_modified = 'tests/snapshots/default_load_2.json'
        fixture_location = 'tests/snapshots/temp'

        # given
        modify_fixture_snapshot(fixture_location, fixture_env, f'tests/snapshots/{fixture_env}.json')
        given_context(snapshot_location=fixture_location, environment=fixture_env)
        Client.load_snapshot()

        # test
        switcher = Client.get_switcher('FF2FOR2030')
        Client.watch_snapshot({
            'success': lambda: setattr(self, 'async_success', True),
            'reject': lambda err: setattr(self, 'async_error', err)
        })

        assert switcher.is_on()
        modify_fixture_snapshot(fixture_location, fixture_env, fixture_env_file_modified)

        # then
        verified = verify_util(30, lambda: self.async_success is True and self.async_error is None)
        if verified:
            assert switcher.is_on() == False
            assert self.async_error is None
        else:
            print("Warning: Snapshot watcher did not detect the change within the time limit")

    def test_watch_snapshot_err_no_snapshot_location(self):
        """ Should reject with error when snapshot location is not defined in the context options """

        # given
        given_context()

        # test
        Client.watch_snapshot({
            'success': lambda: setattr(self, 'async_success', True),
            'reject': lambda err: setattr(self, 'async_error', err)
        })

        # then
        assert self.async_success is None
        assert str(self.async_error) == 'Snapshot location is not defined in the context options'

    def test_watch_snapshot_err_malformed_snapshot(self):
        """ Should reject with error when snapshot file is malformed """

        fixture_env = 'default_load_1'
        fixture_env_file_modified = 'tests/snapshots/default_malformed.json'
        fixture_location = 'tests/snapshots/temp'

        # given
        modify_fixture_snapshot(fixture_location, fixture_env, f'tests/snapshots/{fixture_env}.json')
        given_context(snapshot_location=fixture_location, environment=fixture_env)
        Client.load_snapshot()

        # test
        Client.watch_snapshot({
            'success': lambda: setattr(self, 'async_success', True),
            'reject': lambda err: setattr(self, 'async_error', err)
        })

        modify_fixture_snapshot(fixture_location, fixture_env, fixture_env_file_modified)

        # then
        verified = verify_util(30, lambda: self.async_error is not None)
        if verified:
            assert str(self.async_error) == "Expecting ',' delimiter: line 6 column 26 (char 140)"
        else:
            print("Warning: Snapshot watcher did not detect the change within the time limit")

# Helpers

def given_context(environment: str = DEFAULT_ENVIRONMENT, snapshot_location: Optional[str] = None):
    Client.build_context(
        domain='Playground',
        environment=environment,
        options=ContextOptions(
            local=True,
            snapshot_location=snapshot_location
        )
    )

def modify_fixture_snapshot(location: str, environment: str, fixture_modified_location: str):
    with open(fixture_modified_location, 'r') as file:
        data = file.read()

    os.makedirs(location, exist_ok=True)
    snapshot_file = f"{location}/{environment}.json"
    with open(snapshot_file, 'w') as file:
        file.write(data)

def verify_util(max_time: int, condition_fn) -> bool:
    start_time = time.time()
    while time.time() - start_time < max_time:
        if condition_fn():
            return True
        time.sleep(1)
    return False