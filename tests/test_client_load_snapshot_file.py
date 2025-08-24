import os

from switcher_client import Client, ContextOptions

def test_load_from_snapshot():
    """ Should load Domain from snapshot file """

    Client.build_context(
        domain='My Domain',
        options=ContextOptions(
            local=True,
            snapshot_location='./tests/snapshots'
        )
    )

    # verify initial snapshot version
    assert Client.snapshot_version() == 0

    # test
    version = Client.load_snapshot()
    assert Client.snapshot_version() == 1
    assert version == Client.snapshot_version()

def test_load_from_snapshot_empty():
    """ Should create clean snapshot when no snapshot file exists """

    Client.build_context(
        domain='My Domain',
        environment='generated-clean',
        options=ContextOptions(
            local=True,
            snapshot_location='./tests/snapshots'
        )
    )

    # verify initial snapshot version
    assert Client.snapshot_version() == 0

    # test
    version = Client.load_snapshot()
    assert Client.snapshot_version() == 0
    assert version == Client.snapshot_version()

    # tear down
    delete_snapshot_file('./tests/snapshots', 'generated-clean')
    
# Helpers

def delete_snapshot_file(snapshot_location: str, environment: str):
    snapshot_file = f"{snapshot_location}/{environment}.json"
    if os.path.exists(snapshot_file):
        os.remove(snapshot_file)