from tests.test_switcher_integration import given_context

from switcher_client.lib.snapshot import StrategiesType
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

        Client.assume(self.key).false()
        assert not switcher.is_on()

    def test_switcher_stub_result_details(self):
        """ Should bypass Switcher evaluation and return the stubbed result with details """

        # given
        switcher = Client.get_switcher(self.key)

        # test
        Client.assume(self.key).true()
        result_detail = switcher.is_on_with_details(self.key)
        assert result_detail.result
        assert result_detail.reason == "Forced to True"

    def test_switcher_stub_result_with_metadata(self):
        """ Should bypass Switcher evaluation and return the stubbed result with details and metadata """

        # given
        switcher = Client.get_switcher(self.key)

        # test
        Client.assume(self.key).true().with_metadata({"env": "test", "version": "1.0.0"})

        result_detail = switcher.is_on_with_details(self.key)
        assert result_detail.result
        assert result_detail.reason == "Forced to True"
        assert result_detail.metadata == {"env": "test", "version": "1.0.0"}

    def test_switcher_stub_with_criteria(self):
        """ Should bypass Switcher evaluation based on criteria conditions """

        # given
        switcher = Client.get_switcher(self.key)

        # test
        Client.assume(self.key).true() \
            .when(StrategiesType.VALUE.value, "Canada") \
            .when(StrategiesType.NETWORK.value, "10.0.0.3")

        result_detail = switcher \
            .check_value("Canada") \
            .check_network('10.0.0.3') \
            .is_on_with_details()

        assert result_detail.result
        assert result_detail.reason == "Forced to True"

    def test_switcher_stub_with_unrecheable_criteria(self):
        """ Should bypass Switcher evaluation based on unrecheable criteria conditions """

        # given
        switcher = Client.get_switcher(self.key)

        # test
        Client.assume(self.key).true() \
            .when(StrategiesType.VALUE.value, "Canada")

        result_detail = switcher \
            .check_value("Brazil") \
            .is_on_with_details()

        assert not result_detail.result
        assert result_detail.reason == "Forced to False when: [Canada] - input: Brazil"

    def test_switcher_stub_with_multiple_criteria(self):
        """ Should bypass Switcher evaluation based on multiple criteria conditions """

        # given
        switcher = Client.get_switcher(self.key)

        # test
        Client.assume(self.key).true() \
            .when(StrategiesType.VALUE.value, ["Canada", "Brazil"])

        assert switcher.check_value("Canada").is_on()
        assert switcher.check_value("Brazil").is_on()
        assert not switcher.check_value("USA").is_on()