from tests.test_switcher_integration import given_context

from switcher_client.client import Client, ContextOptions

context_options_local = ContextOptions(snapshot_location='tests/snapshots', local=True, logger=True)

class TestSwitcherStub:
    """ Test suite for SwitcherStub (Bypasser) - Client.assume() """

    key = 'FF2FOR2020'

    def setup_method(self):
        given_context(options=context_options_local)
        Client.load_snapshot()

    def teardown_method(self):
        Client.forget(self.key)

    def test_switcher_stub_result(self):
        """ Should bypass Switcher evaluation and return the stubbed result """

        # given
        switcher = Client.get_switcher(self.key)

        # test
        Client.assume(self.key).true()

        assert switcher.is_on()