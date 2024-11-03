import pytest

from switcher_client import Client

def test_context():
    Client.build_context(
        domain='My Domain',
        url='https://api.switcherapi.com',
        api_key='[API_KEY]',
        component='MyApp'
    )

    try:
        Client.verify_context()
    except ValueError as e:
        pytest.fail(f'Context verification failed: {e}')

def test_clear_context():
    Client.build_context(
        domain='My Domain',
        url='https://api.switcherapi.com',
        api_key='[API_KEY]',
        component='MyApp'
    )

    Client.clear_context()

    with pytest.raises(ValueError):
        Client.verify_context()
