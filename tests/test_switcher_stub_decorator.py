import asyncio
import pytest

from contextvars import Context

from tests.test_switcher_integration import given_context
from switcher_client import Client, ContextOptions, StrategiesType, assume_test, switcher_test

context_options_local = ContextOptions(snapshot_location='tests/snapshots', local=True, logger=True)
PRIMARY_KEY = 'FF2FOR2020'
SECONDARY_KEY = 'FF2FOR2022'

@pytest.fixture(autouse=True)
def local_context():
    given_context(options=context_options_local)
    Client.load_snapshot()
    yield
    Client.clear_resources()

def test_switcher_test_applies_and_cleans_up_mocked_value():
    """ Should apply the mocked value during the test and clean up after the test, even if the test fails. """
    @switcher_test(assume_test(PRIMARY_KEY).true())
    def decorated_test():
        return Client.get_switcher(PRIMARY_KEY).reset_inputs().is_on()

    assert decorated_test() is True
    assert Client.get_switcher(PRIMARY_KEY).reset_inputs().is_on() is False

def test_switcher_test_requires_at_least_one_assumption():
    """ Should raise an error when no assumptions are provided. """
    with pytest.raises(ValueError, match='requires at least one test assumption'):
        @switcher_test()
        def decorated_test():
            """ This test should never run because the decorator should raise an error due to missing assumptions. """
            pass

def test_switcher_test_requires_assume_test_builders():
    """ Should raise an error when assumptions are not created with assume_test. """
    with pytest.raises(TypeError, match='expects values created with assume_test'):
        @switcher_test(PRIMARY_KEY) # type: ignore
        def decorated_test():
            """ This test should never run because the decorator should raise an error due to invalid assumptions. """
            pass

def test_switcher_test_cleans_up_when_test_fails():
    """ Should clean up mocked value even if the test raises an exception. """
    @switcher_test(assume_test(PRIMARY_KEY).true())
    def decorated_test():
        assert Client.get_switcher(PRIMARY_KEY).reset_inputs().is_on() is True
        raise RuntimeError('boom')

    with pytest.raises(RuntimeError, match='boom'):
        decorated_test()

    assert Client.get_switcher(PRIMARY_KEY).reset_inputs().is_on() is False

def test_switcher_test_rolls_back_applied_mocks_when_setup_fails(monkeypatch: pytest.MonkeyPatch):
    """ Should forget already-applied assumptions when a later assumption fails during setup. """
    original_assume = Client.assume

    def flaky_assume(key: str):
        if key == SECONDARY_KEY:
            raise RuntimeError('setup failed')
        return original_assume(key)

    monkeypatch.setattr(Client, 'assume', staticmethod(flaky_assume))

    @switcher_test(
        assume_test(PRIMARY_KEY).true(),
        assume_test(SECONDARY_KEY).false()
    )
    def decorated_test():
        """ This test should never run because setup fails before execution. """
        assert False

    with pytest.raises(RuntimeError, match='setup failed'):
        decorated_test()

    assert Client.get_switcher(PRIMARY_KEY).reset_inputs().is_on() is False

def test_switcher_test_supports_conditional_mocks():
    """ Should support conditional mocks based on strategies. """
    @switcher_test(
        assume_test(PRIMARY_KEY)
            .true()
            .when(StrategiesType.VALUE.value, 'Canada')
            .when(StrategiesType.NETWORK.value, '10.0.0.3')
    )
    def decorated_test():
        result_detail = Client.get_switcher(PRIMARY_KEY) \
            .check_value('Canada') \
            .check_network('10.0.0.3') \
            .is_on_with_details()

        assert result_detail.result is True
        assert result_detail.reason == 'Forced to True'

    decorated_test()

def test_switcher_test_supports_metadata():
    """ Should support metadata in mocked values. """
    @switcher_test(
        assume_test(PRIMARY_KEY)
            .false()
            .with_metadata({'message': 'Feature is disabled'})
    )
    def decorated_test():
        result_detail = Client.get_switcher(PRIMARY_KEY).reset_inputs().is_on_with_details()

        assert result_detail.result is False
        assert result_detail.metadata == {'message': 'Feature is disabled'}

    decorated_test()

def test_switcher_test_supports_multiple_mocked_flags():
    """ Should support mocking multiple flags in the same test. """
    @switcher_test(
        assume_test(PRIMARY_KEY).true(),
        assume_test(SECONDARY_KEY).false()
    )
    def decorated_test():
        assert Client.get_switcher(PRIMARY_KEY).reset_inputs().is_on() is True
        assert Client.get_switcher(SECONDARY_KEY).reset_inputs().is_on() is False

    decorated_test()

    assert Client.get_switcher(PRIMARY_KEY).reset_inputs().is_on() is False
    assert Client.get_switcher(SECONDARY_KEY).reset_inputs().is_on() is True

def test_switcher_test_keeps_mocks_scoped_to_the_current_execution_context():
    """ Should keep mocks scoped to the current execution context. """
    @switcher_test(assume_test(PRIMARY_KEY).true())
    def decorated_test():
        isolated_result = Context().run(
            lambda: Client.get_switcher(PRIMARY_KEY).reset_inputs().is_on()
        )

        assert Client.get_switcher(PRIMARY_KEY).reset_inputs().is_on() is True
        assert isolated_result is False

    decorated_test()

def test_switcher_test_supports_async_tests():
    """ Should support async tests. """
    @switcher_test(assume_test(PRIMARY_KEY).true())
    async def decorated_test():
        await asyncio.sleep(0)
        return Client.get_switcher(PRIMARY_KEY).reset_inputs().is_on()

    assert asyncio.run(decorated_test()) is True
    assert Client.get_switcher(PRIMARY_KEY).reset_inputs().is_on() is False
