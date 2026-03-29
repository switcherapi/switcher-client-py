import os

from dotenv import load_dotenv

from switcher_client.client import Client
from switcher_client.lib.globals.global_context import ContextOptions
from switcher_client.lib.globals.global_snapshot import LoadSnapshotOptions

load_dotenv()
API_KEY = os.getenv('SWITCHER_API_KEY')
WARN_SKIP = 'API key not found. Please set the SWITCHER_API_KEY environment variable.'

def test_is_on():
    """ Should call the remote API with success """

    if not API_KEY:
        print(WARN_SKIP)
        return

    # given
    given_context()
    switcher = Client.get_switcher('CLIENT_PYTHON_FEATURE')

    # test
    response_detail = switcher.is_on_with_details()
    assert response_detail is not None

def test_load_snapshot():
    """ Should load the snapshot from the remote API with success """

    if not API_KEY:
        print(WARN_SKIP)
        return

    # given
    given_context(options=ContextOptions(local=True))

    # test
    snapshot = Client.load_snapshot(options=LoadSnapshotOptions(fetch_remote=True))
    switcher = Client.get_switcher('CLIENT_PYTHON_FEATURE')
    response_detail = switcher.is_on_with_details()

    assert snapshot is not None
    assert response_detail is not None

def test_check_switcher_availability():
    """ Should check the switcher availability with success """

    if not API_KEY:
        print(WARN_SKIP)
        return

    # given
    given_context()

    # test
    try:
        Client.check_switchers(['CLIENT_PYTHON_FEATURE'])
    except Exception as e:
        assert False, f'check_switchers should not raise an exception, but got: {e}'

# Helpers

def given_context(options=ContextOptions()):
    Client.build_context(
        url='https://api.switcherapi.com',
        api_key=API_KEY,
        domain='Switcher API',
        component='switcher-client-python',
        options=options
    )