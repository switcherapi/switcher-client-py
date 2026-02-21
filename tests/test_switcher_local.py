import json

from time import time

from switcher_client.client import Client, ContextOptions
from switcher_client.errors import LocalCriteriaError
from switcher_client.lib.utils.timed_match.timed_match import DEFAULT_REGEX_MAX_BLACKLISTED, DEFAULT_REGEX_MAX_TIME_LIMIT

async_error = None

def test_local():
    """ Should use local Snapshot to evaluate the switcher """

    # given
    given_context('tests/snapshots')
    snapshot_version = Client.load_snapshot()

    switcher = Client.get_switcher()

    # test
    assert snapshot_version == 1
    assert switcher.is_on('FF2FOR2022')

def test_local_with_strategy():
    """ Should use local Snapshot to evaluate the switcher with strategy """

    # given
    given_context('tests/snapshots')
    Client.load_snapshot()

    switcher = Client.get_switcher()

    # test
    assert switcher \
        .check_value('Japan') \
        .check_network('10.0.0.3') \
        .is_on('FF2FOR2020')
    
def test_local_with_strategy_payload():
    """ Should use local Snapshot to evaluate the switcher with payload validation strategy """

    # given
    given_context('tests/snapshots')
    Client.load_snapshot()

    switcher = Client.get_switcher()
    payload = {
        'id': 12345, 
        'user': {
            'login': 'test_user',
            'role': 'admin'
        }
    }

    # test (using stringified JSON)
    assert switcher \
        .check_payload(json.dumps(payload)) \
        .is_on('FF2FOR2023')
    
    # test (using dict)
    assert switcher \
        .check_payload(payload) \
        .is_on('FF2FOR2023')

def test_local_with_strategy_no_input():
    """ Should return disabled when no input is provided for the strategy """

    # given
    given_context('tests/snapshots')
    Client.load_snapshot()

    switcher = Client.get_switcher()

    # test
    assert switcher.is_on('FF2FOR2020') is False

def test_local_with_strategy_no_matching_input():
    """ Should return disabled when no matching input is provided for the strategy """

    # given
    given_context(snapshot_location='tests/snapshots', regex_max_time_limit=100)
    Client.load_snapshot()

    switcher = Client.get_switcher()

    # test
    assert switcher \
        .check_regex('123') \
        .is_on('FF2FOR2024') is False
    
    # teardown
    Client.clear_resources()

def test_local_with_strategy_redos_input():
    """ Should return disabled when ReDoS input is provided for the strategy """

    # given
    regex_input = 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
    given_context(snapshot_location='tests/snapshots', 
                  regex_max_black_list=1,
                  regex_max_time_limit=100)
    Client.load_snapshot()

    switcher = Client.get_switcher()

    # test
    current_time_ms = int(time() * 1000)
    assert switcher \
        .check_regex(regex_input) \
        .is_on('FF2FOR2024') is False
    elapsed_time_ms = int(time() * 1000) - current_time_ms
    assert elapsed_time_ms < 150 # Within TimedMatch time limit (100ms) + margin

    # test blacklisted input
    current_time_ms = int(time() * 1000)
    assert switcher \
        .check_regex(regex_input) \
        .is_on('FF2FOR2024') is False
    elapsed_time_ms = int(time() * 1000) - current_time_ms
    assert elapsed_time_ms < 50  # Should be fast on second attempt due to blacklist

    # teardown
    Client.clear_resources()

def test_local_domain_disabled():
    """ Should return disabled when domain is deactivated """

    # given
    given_context('tests/snapshots', environment='default_disabled')
    snapshot_version = Client.load_snapshot()

    switcher = Client.get_switcher()

    # test
    assert snapshot_version == 1
    assert switcher.is_on('FEATURE') is False

def test_local_group_disabled():
    """ Should return disabled when group is deactivated """

    # given
    given_context('tests/snapshots')
    snapshot_version = Client.load_snapshot()

    switcher = Client.get_switcher()

    # test
    assert snapshot_version == 1
    assert switcher.is_on('FF2FOR2040') is False

def test_local_config_disabled():
    """ Should return disabled when config is deactivated """

    # given
    given_context('tests/snapshots')
    snapshot_version = Client.load_snapshot()

    switcher = Client.get_switcher()

    # test
    assert snapshot_version == 1
    assert switcher.is_on('FF2FOR2031') is False

def test_local_strategy_disabled():
    """ Should return disabled when strategy is deactivated """

    # given
    given_context('tests/snapshots')
    snapshot_version = Client.load_snapshot()

    switcher = Client.get_switcher()

    # test
    assert snapshot_version == 1
    assert switcher.check_network('10.0.0.3').is_on('FF2FOR2021')

def test_local_no_key_found():
    """ Should raise an error when no key is found in the snapshot """

    # given
    given_context('tests/snapshots')
    snapshot_version = Client.load_snapshot()

    switcher = Client.get_switcher()

    # test
    assert snapshot_version == 1
    try:
        switcher.is_on('INVALID_KEY')
    except LocalCriteriaError as e:
        assert str(e) == "Config with key 'INVALID_KEY' not found in the snapshot"

def test_local_err_check_criteria_default_result():
    """ Should return default result when check criteria fails """

    # given
    given_context('tests/snapshots')
    snapshot_version = Client.load_snapshot()

    globals().update(async_error=None)
    Client.subscribe_notify_error(lambda error: globals().update(async_error=str(error)))
    switcher = Client.get_switcher()

    # test
    assert snapshot_version == 1
    
    feature = switcher.default_result(True).is_on_with_details('INVALID_KEY')
    assert feature.result is True
    assert feature.reason == 'Default result'
    assert async_error == "Config with key 'INVALID_KEY' not found in the snapshot"

def test_local_no_snapshot():
    """ Should raise an error when no snapshot is loaded """

    # given
    given_context('tests/invalid_location')
    switcher = Client.get_switcher()

    # test
    try:
        switcher.is_on('FF2FOR2022')
    except LocalCriteriaError as e:
        assert str(e) == "Snapshot not loaded. Try to use 'Client.load_snapshot()'"

# Helpers

def given_context(snapshot_location: str, environment: str = 'default', 
                  regex_max_black_list = DEFAULT_REGEX_MAX_BLACKLISTED,
                  regex_max_time_limit = DEFAULT_REGEX_MAX_TIME_LIMIT):
    Client.build_context(
        domain='Playground',
        environment=environment,
        options=ContextOptions(
            local=True,
            logger=True,
            snapshot_location=snapshot_location,
            regex_max_black_list=regex_max_black_list,
            regex_max_time_limit=regex_max_time_limit
        )
    )