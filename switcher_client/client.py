from typing import Optional, Callable

from .lib.globals.global_snapshot import GlobalSnapshot, LoadSnapshotOptions
from .lib.globals.global_context import Context, ContextOptions, DEFAULT_ENVIRONMENT
from .lib.remote_auth import RemoteAuth
from .lib.snapshot_auto_updater import SnapshotAutoUpdater
from .lib.snapshot_loader import load_domain, validate_snapshot, save_snapshot
from .lib.utils.execution_logger import ExecutionLogger
from .lib.utils.timed_match.timed_match import TimedMatch
from .lib.utils import get
from .switcher import Switcher

class SwitcherOptions:
    REGEX_MAX_BLACK_LIST = 'regex_max_black_list'
    REGEX_MAX_TIME_LIMIT = 'regex_max_time_limit'
    SNAPSHOT_AUTO_UPDATE_INTERVAL = 'snapshot_auto_update_interval'
    SILENT_MODE = 'silent_mode'

class Client:
    _context: Context = Context.empty()
    _switcher: dict[str, Switcher] = {}

    @staticmethod
    def build_context(
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
        Client._context = Context(domain, url, api_key, component, environment, options)

        # Default values
        GlobalSnapshot.clear()

        # Build Options
        if options is not None:
            Client._build_options(options)

        # Initialize Auth
        RemoteAuth.init(Client._context)

    @staticmethod
    def _build_options(options: ContextOptions):
        options_handler = {
            SwitcherOptions.SNAPSHOT_AUTO_UPDATE_INTERVAL: lambda: Client.schedule_snapshot_auto_update(),
            SwitcherOptions.SILENT_MODE: lambda: Client._init_silent_mode(get(options.silent_mode, '')),
            SwitcherOptions.REGEX_MAX_BLACK_LIST: lambda: TimedMatch.set_max_blacklisted(options.regex_max_black_list),
            SwitcherOptions.REGEX_MAX_TIME_LIMIT: lambda: TimedMatch.set_max_time_limit(options.regex_max_time_limit)
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
            SnapshotAutoUpdater.schedule(
                interval=Client._context.options.snapshot_auto_update_interval,
                check_snapshot=Client.check_snapshot,
                callback=callback
            )
    
    @staticmethod
    def terminate_snapshot_auto_update():
        """ Terminate Snapshot auto update """
        SnapshotAutoUpdater.terminate()

    @staticmethod
    def snapshot_version() -> int:
        """ Get the version of the snapshot """
        snapshot = GlobalSnapshot.snapshot()

        if snapshot is None:
            return 0
        
        return snapshot.domain.version

    @staticmethod
    def get_execution(switcher: Switcher) -> ExecutionLogger:
        """Retrieve execution log given a switcher"""
        return ExecutionLogger.get_execution(switcher._key, switcher._input)

    @staticmethod
    def clear_logger() -> None:
        """Clear all logged executions"""
        ExecutionLogger.clear_logger()

    @staticmethod
    def clear_resources() -> None:
        """ Clear all resources used by the Client """
        Client.terminate_snapshot_auto_update()
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
    def _is_check_snapshot_available(fetch_remote = False) -> bool:
        return Client.snapshot_version() == 0 and (fetch_remote or not Client._context.options.local)