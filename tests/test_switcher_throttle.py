import time

from tests.helpers import given_context, given_auth, given_check_criteria

from switcher_client import Client
from switcher_client.lib.globals.global_context import ContextOptions

context_options = ContextOptions(
    throttle_max_workers=2,
    freeze=False
)

def test_throttle(httpx_mock):
    """ Should throttle remote API calls and use cached response """

    # given
    key = 'MY_SWITCHER_THROTTLE'
    given_auth(httpx_mock)
    given_check_criteria(httpx_mock, key=key, show_details=True, response={'result': True})
    given_context(options=context_options)

    switcher = Client.get_switcher()
    switcher.throttle(1000)  # 1 second throttle

    # test
    response = switcher.is_on_with_details(key)
    assert response.result is True
    assert response.metadata == {}

    # when - call again within throttle period (no new API call should be made, cached response should be used)
    response = switcher.is_on_with_details(key)
    assert switcher.is_on(key) is True
    assert response.result is True
    assert response.metadata == {'cached': True}

    time.sleep(1)

    # when - call again outside of throttle period (new API call should be made, cached response should be updated)
    given_check_criteria(httpx_mock, key=key, show_details=True, response={'result': False})
    response = switcher.is_on_with_details(key)
    assert response.result is False
    assert response.metadata == {'cached': True}

def test_throttle_with_freeze_options(httpx_mock):
    """ Should prevents the background execution when using throttle with freeze option as True """

    key = 'MY_SWITCHER_THROTTLE_FREEZE'
    options = ContextOptions(**vars(context_options))
    options.freeze = True

    # given
    given_auth(httpx_mock)
    given_check_criteria(httpx_mock, key=key, show_details=True, response={'result': True})
    given_context(options=options)

    switcher = Client.get_switcher()
    switcher.throttle(1000)  # 1 second throttle

    # test
    response = switcher.is_on_with_details(key)
    assert response.result is True
    assert response.metadata == {}

    time.sleep(1)

    # when - call again outside of throttle period (cached response should NOT be updated, unless we use Client.clear_logger())
    response = switcher.is_on_with_details(key)
    assert response.result is True
    assert response.metadata == {'cached': True}
