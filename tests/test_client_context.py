import pytest

from switcher_client import Client, ContextOptions

def test_context():
    """ Should build and verify context """

    Client.build_context(
        domain='My Domain',
        url='https://api.switcherapi.com',
        api_key='[API_KEY]',
        component='MyApp'
    )

    try:
        Client.verify_context()

        assert Client.context.domain == 'My Domain'
        assert Client.context.url == 'https://api.switcherapi.com'
        assert Client.context.api_key == '[API_KEY]'
        assert Client.context.component == 'MyApp'
    except ValueError as e:
        pytest.fail(f'Context verification failed: {e}')

def test_clear_context():
    """ Should clear context """

    Client.build_context(
        domain='My Domain',
        url='https://api.switcherapi.com',
        api_key='[API_KEY]',
        component='MyApp'
    )

    Client.clear_context()

    with pytest.raises(ValueError):
        Client.verify_context()

def test_context_with_optionals():
    """ Should build context with optional parameters - local and snapshot_location """

    Client.build_context(
        domain='My Domain',
        options=ContextOptions(
            local=True,
            snapshot_location='./tests/snapshots'
        )
    )

    options = Client.context.options

    assert options.local == True
    assert options.snapshot_location == './tests/snapshots'
