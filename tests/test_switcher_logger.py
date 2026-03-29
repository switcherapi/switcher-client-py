from tests.helpers import given_context, given_auth, given_check_criteria

from switcher_client import Client
from switcher_client.lib.globals.global_context import ContextOptions
from switcher_client.lib.utils.execution_logger import ExecutionLogger

context_options_logger = ContextOptions(logger=True)

def test_remote_with_logger(httpx_mock):
    """ Should log remote calls successfully """

    # given
    given_auth(httpx_mock)
    given_check_criteria(httpx_mock, response={'result': True})
    given_context(options=context_options_logger)

    switcher = Client.get_switcher()

    # test
    assert switcher.is_on('MY_SWITCHER')

    logged = Client.get_execution(switcher)
    assert logged.key == 'MY_SWITCHER'
    assert logged.response.result is True

    # test by key
    logged_by_key = ExecutionLogger.get_by_key('MY_SWITCHER')
    assert len(logged_by_key) == 1
    assert logged_by_key[0].key == 'MY_SWITCHER'
    assert logged_by_key[0].response.result is True

def test_clear_logger(httpx_mock):
    """ Should clear logged executions """

    # given
    given_auth(httpx_mock)
    given_check_criteria(httpx_mock, response={'result': True})
    given_context(options=context_options_logger)

    switcher = Client.get_switcher()

    # test
    assert switcher.is_on('MY_SWITCHER')

    # test clear
    Client.clear_logger()
    logged = Client.get_execution(switcher)
    assert logged.key is None


def test_remote_with_input_and_logger(httpx_mock):
    """ Should log remote calls with input successfully """

    # given
    given_auth(httpx_mock)
    given_check_criteria(httpx_mock, response={'result': True}, match={
        'entry': [{
            'strategy': 'VALUE_VALIDATION',
            'input': 'user_id'
        }]
    })
    given_context(options=context_options_logger)

    switcher = Client.get_switcher()

    # test
    assert switcher \
        .check_value('user_id') \
        .is_on('MY_SWITCHER')

    logged = Client.get_execution(switcher)
    assert logged.key == 'MY_SWITCHER'
    assert logged.response.result is True
    assert logged.input == [['VALUE_VALIDATION', 'user_id']]

def test_remote_with_input_not_logged(httpx_mock):
    """ Should not find logged execution for different input """

    # given
    given_auth(httpx_mock)
    given_check_criteria(httpx_mock, response={'result': True}, match={
        'entry': [{
            'strategy': 'VALUE_VALIDATION',
            'input': 'user_id'
        }]
    })
    given_context(options=context_options_logger)

    switcher = Client.get_switcher()

    # test
    assert switcher \
        .check_value('user_id') \
        .is_on('MY_SWITCHER')

    logged = Client.get_execution(Client.get_switcher('MY_SWITCHER').check_value('other_id'))
    assert logged.key is None

def test_remote_renew_logged_execution(httpx_mock):
    """ Should renew logged execution when new response is received """

    # given
    given_auth(httpx_mock)
    given_check_criteria(httpx_mock, response={'result': True})
    given_context(options=context_options_logger)

    switcher = Client.get_switcher()

    # test 1
    assert switcher.is_on('MY_SWITCHER')

    logged = Client.get_execution(switcher)
    assert logged.key == 'MY_SWITCHER'
    assert logged.response.result is True

    # test 2 - change response
    given_check_criteria(httpx_mock, response={'result': False})
    assert switcher.is_on('MY_SWITCHER') is False

    logged = Client.get_execution(switcher)
    assert logged.key == 'MY_SWITCHER'
    assert logged.response.result is False

def test_execution_logger_not_found(httpx_mock):
    """ Should return empty logger when not found"""

    # given
    given_auth(httpx_mock)
    given_check_criteria(httpx_mock, response={'result': True})
    given_context(options=context_options_logger)

    switcher = Client.get_switcher()

    # test
    assert switcher.is_on('MY_SWITCHER')

    logged = Client.get_execution(Client.get_switcher('ANOTHER_SWITCHER'))
    assert logged.key is None
