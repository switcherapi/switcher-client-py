from typing import Optional, Callable

from switcher_client.lib.bypasser import Bypasser, Key
from switcher_client.lib.globals.global_auth import GlobalAuth
from switcher_client.lib.globals.global_snapshot import GlobalSnapshot, LoadSnapshotOptions
from switcher_client.lib.globals.global_context import Context, ContextOptions, DEFAULT_ENVIRONMENT, DEFAULT_TEST_MODE
from switcher_client.lib.remote_auth import RemoteAuth
from switcher_client.lib.remote import Remote
from switcher_client.lib.snapshot_auto_updater import SnapshotAutoUpdater
from switcher_client.lib.snapshot_loader import check_switchers, load_domain, validate_snapshot, save_snapshot
from switcher_client.lib.snapshot_watcher import SnapshotWatcher, WatchSnapshotCallback
from switcher_client.lib.utils.execution_logger import ExecutionLogger
from switcher_client.lib.utils.timed_match.timed_match import TimedMatch
from switcher_client.lib.utils import get
from switcher_client.errors import SnapshotNotFoundError, TestModeError
from switcher_client.switcher import Switcher

REGEX_MAX_BLACK_LIST = 'regex_max_black_list'
REGEX_MAX_TIME_LIMIT = 'regex_max_time_limit'
SNAPSHOT_AUTO_UPDATE_INTERVAL = 'snapshot_auto_update_interval'
SILENT_MODE = 'silent_mode'

class Client:
    """
    Quick start with the following steps:

    1. Use `Client.build_context()` to build the context for the client.
    2. Use `Client.get_switcher()` to create a new instance of Switcher.
    3. Use the instance created to evaluate criteria.

        Example:
            Client.build_context(
                domain='My Domain',                 # Your Switcher domain name
                url='https://api.switcherapi.com',  # Switcher-API endpoint (optional)
                api_key='[YOUR_API_KEY]',           # Your component's API key (optional)
                component='MyApp',                  # Your application name (optional)
                environment='default'               # Environment ('default' for production)
            )

            switcher = Client.get_switcher()
            result = switcher.is_on('my_criteria')
    """
    _context: Context = Context.empty()
    _switcher: dict[str, Switcher] = {}
    _snapshot_auto_updater: SnapshotAutoUpdater = SnapshotAutoUpdater()
    _snapshot_watcher: SnapshotWatcher = SnapshotWatcher()
    _test_mode: bool = DEFAULT_TEST_MODE

    # pylint: disable=too-many-arguments
    @staticmethod
    def build_context(*,
        domain: str,
        url: Optional[str] = None,
        api_key: Optional[str] = None,
        component: Optional[str] = None,
        environment: Optional[str] = DEFAULT_ENVIRONMENT,
        options = ContextOptions()):
        """
        Build the context for the client

        :param domain: Domain name
        :param url:Switcher-API URL
        :param api_key: Switcher-API key generated for the application/component
        :param component: Application/component name
        :param environment: Environment name
        :param options: Optional parameters

        """
        Client._context = Context(
            domain=domain, url=url,
            api_key=api_key,
            component=component,
            environment=environment,
            options=options)

        # Default values
        Client._test_mode = DEFAULT_TEST_MODE
        GlobalSnapshot.clear()

        # Build Options
        if options is not None:
            Client._build_options(options)

        # Initialize Auth
        RemoteAuth.init(Client._context)

    @staticmethod
    def _build_options(options: ContextOptions):
        options_handler = {
            SNAPSHOT_AUTO_UPDATE_INTERVAL: Client.schedule_snapshot_auto_update,
            SILENT_MODE: lambda: Client._init_silent_mode(get(options.silent_mode, '')),
            REGEX_MAX_BLACK_LIST: lambda: TimedMatch.set_max_blacklisted(options.regex_max_black_list),
            REGEX_MAX_TIME_LIMIT: lambda: TimedMatch.set_max_time_limit(options.regex_max_time_limit)
        }

        for option_key, handler in options_handler.items():
            if hasattr(options, option_key) and getattr(options, option_key) is not None:
                handler()

    @staticmethod
    def _init_silent_mode(silent_mode: str):
        if silent_mode != '':
            RemoteAuth.set_retry_options(silent_mode)
            Client._context.options.silent_mode = silent_mode
            Client.load_snapshot()

    @staticmethod
    def get_switcher(key: Optional[str] = None) -> Switcher:
        """
        Creates a new instance of Switcher.
        Provide a key if you want to persist the instance.
        """
        key_value = get(key, '')
        persisted_switcher = Client._switcher.get(key_value)

        if persisted_switcher is not None:
            return persisted_switcher

        switcher = Switcher(Client._context, key_value) \
            .restrict_relay(Client._context.options.restrict_relay)

        if key_value != '':
            Client._switcher[key_value] = switcher

        return switcher


    @staticmethod
    def load_snapshot(options: Optional[LoadSnapshotOptions] = None) -> int:
        """ Load Domain from snapshot """
        snapshot_options = get(options, LoadSnapshotOptions())

        GlobalSnapshot.init(load_domain(
            get(Client._context.options.snapshot_location, ''),
            get(Client._context.environment, DEFAULT_ENVIRONMENT)
        ))

        if Client._is_check_snapshot_available(snapshot_options.fetch_remote):
            Client.check_snapshot()

        return Client.snapshot_version()

    @staticmethod
    def check_snapshot():
        """ Verifies if the current snapshot file is updated
            Return true if an update has been made
        """

        if RemoteAuth.is_token_expired():
            RemoteAuth.auth()

        snapshot = validate_snapshot(
            context=Client._context,
            snapshot_version=Client.snapshot_version(),
        )

        if snapshot is not None:
            if Client._context.options.snapshot_location is not None:
                save_snapshot(
                    snapshot=snapshot,
                    snapshot_location=get(Client._context.options.snapshot_location, ''),
                    environment=get(Client._context.environment, DEFAULT_ENVIRONMENT)
                )

            GlobalSnapshot.init(snapshot)
            return True

        return False

    @staticmethod
    def schedule_snapshot_auto_update(interval: Optional[int] = None,
                                      callback: Optional[Callable[[Optional[Exception], bool], None]] = None):
        """ Schedule Snapshot auto update """
        callback = get(callback, lambda *_: None)

        if interval is not None:
            Client._context.options.snapshot_auto_update_interval = interval

        if Client._context.options.snapshot_auto_update_interval is not None and \
            Client._context.options.snapshot_auto_update_interval > 0:
            Client._snapshot_auto_updater.schedule(
                interval=Client._context.options.snapshot_auto_update_interval,
                check_snapshot=Client.check_snapshot,
                callback=callback
            )

    @staticmethod
    def terminate_snapshot_auto_update():
        """ Terminate Snapshot auto update """
        Client._snapshot_auto_updater.terminate()

    @staticmethod
    def watch_snapshot(callback: Optional[WatchSnapshotCallback] = None) -> None:
        """ Watch snapshot file for changes and invoke callbacks on result """
        callback = get(callback, WatchSnapshotCallback())
        snapshot_location = Client._context.options.snapshot_location

        if Client._test_mode:
            callback.reject(TestModeError("Snapshot watcher is not available in test mode"))
            return

        if snapshot_location is None:
            callback.reject(SnapshotNotFoundError("Snapshot location is not defined in the context options"))
            return

        environment = get(Client._context.environment, DEFAULT_ENVIRONMENT)
        Client._snapshot_watcher.watch_snapshot(snapshot_location, environment, callback)

    @staticmethod
    def unwatch_snapshot() -> None:
        """ Stop watching the snapshot file """
        Client._snapshot_watcher.unwatch_snapshot()

    @staticmethod
    def snapshot_version() -> int:
        """ Get the version of the snapshot """
        snapshot = GlobalSnapshot.snapshot()

        if snapshot is None:
            return 0

        return snapshot.domain.version

    @staticmethod
    def check_switchers(switcher_keys: list[str]) -> None:
        """ Verifies if switchers are properly configured """
        if Client._context.options.local:
            check_switchers(GlobalSnapshot.snapshot(), switcher_keys)
        else:
            Client._check_switchers_remote(switcher_keys)

    @staticmethod
    def get_execution(switcher: Switcher) -> ExecutionLogger:
        """Retrieve execution log given a switcher"""
        return ExecutionLogger.get_execution(switcher.key, switcher.inputs)

    @staticmethod
    def clear_logger() -> None:
        """Clear all logged executions"""
        ExecutionLogger.clear_logger()

    @staticmethod
    def clear_resources() -> None:
        """ Clear all resources used by the Client """
        Client.terminate_snapshot_auto_update()
        Client.unwatch_snapshot()
        ExecutionLogger.clear_logger()
        GlobalSnapshot.clear()
        TimedMatch.terminate_worker()

    @staticmethod
    def subscribe_notify_error(callback: Callable[[Exception], None]) -> None:
        """
        Subscribe to notify when an asynchronous error is thrown.
        It is usually used when throttle and silent mode are enabled.
        """
        ExecutionLogger.subscribe_notify_error(callback)

    @staticmethod
    def assume(key: str) -> Key:
        """ Force a switcher value to return a given value by calling one of both methods - true() false() """
        return Bypasser.assume(key)

    @staticmethod
    def forget(key: str) -> None:
        """ Remove forced value from a switcher """
        Bypasser.forget(key)

    @staticmethod
    def test_mode() -> None:
        """ It prevents subprocess to run during tests such as snapshot watcher """
        Client._test_mode = True

    @staticmethod
    def _is_check_snapshot_available(fetch_remote = False) -> bool:
        return Client.snapshot_version() == 0 and (fetch_remote or not Client._context.options.local)

    @staticmethod
    def _check_switchers_remote(switcher_keys: list[str]) -> None:
        RemoteAuth.auth()
        Remote.check_switchers(
            token=GlobalAuth.get_token(),
            switcher_keys=switcher_keys,
            context=Client._context)
