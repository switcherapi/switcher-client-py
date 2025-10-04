import pytest
import time

from typing import Optional
from pytest_httpx import HTTPXMock

from switcher_client import Client, ContextOptions

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

def test_context_remote_validation():
    """ Should raise error when missing required fields for remote """
    
    Client.build_context(
        domain='My Domain'
    )

    # test
    with pytest.raises(ValueError) as excinfo:
        Client.get_switcher().validate() # used by is_on()
    
    assert 'Missing or empty required fields (url, component, api_key)' in str(excinfo.value)

# Helpers

def given_auth(httpx_mock: HTTPXMock, status=200, token: Optional[str]='[token]', exp=int(round(time.time() * 1000))):
    httpx_mock.add_response(
        url='https://api.switcherapi.com/criteria/auth',
        method='POST',
        status_code=status,
        json={'token': token, 'exp': exp}
    )