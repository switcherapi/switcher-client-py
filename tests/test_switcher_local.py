from switcher_client.client import Client, ContextOptions
from switcher_client.errors import LocalCriteriaError

def test_local():
    """ Should use local Snapshot to evaluate the switcher """

    # given
    given_context('tests/snapshots')
    snapshot_version = Client.load_snapshot()

    switcher = Client.get_switcher()

    # test
    assert snapshot_version == 1
    assert switcher.is_on('FF2FOR2022')

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

def given_context(snapshot_location: str, environment: str = 'default') -> None:
    Client.build_context(
        domain='Playground',
        environment=environment,
        options=ContextOptions(
            local=True,
            snapshot_location=snapshot_location
        )
    )