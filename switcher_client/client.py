from typing import Optional, Callable

from .lib.globals.global_snapshot import GlobalSnapshot, LoadSnapshotOptions
from .lib.remote_auth import RemoteAuth
from .lib.globals.global_context import Context, ContextOptions
from .lib.globals.global_context import DEFAULT_ENVIRONMENT
from .lib.snapshot_auto_updater import SnapshotAutoUpdater
from .lib.snapshot_loader import load_domain, validate_snapshot, save_snapshot
from .lib.utils.execution_logger import ExecutionLogger
from .lib.utils.timed_match.timed_match import TimedMatch
from .lib.utils import get
from .switcher import Switcher

class SwitcherOptions:
    SNAPSHOT_AUTO_UPDATE_INTERVAL = 'snapshot_auto_update_interval'

class Client:
    context: Context = Context.empty()

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
        Client.context = Context(domain, url, api_key, component, environment, options)

        # Default values
        GlobalSnapshot.clear()

        # Build Options
        if options is not None:
            Client._build_options(options)

        # Initialize Auth
        RemoteAuth.init(Client.context)

    @staticmethod
    def _build_options(options: ContextOptions):
        options_handler = {
            SwitcherOptions.SNAPSHOT_AUTO_UPDATE_INTERVAL: lambda: Client.schedule_snapshot_auto_update()
        }
        
        for option_key, handler in options_handler.items():
            if hasattr(options, option_key) and getattr(options, option_key) is not None:
                handler()

    @staticmethod
    def get_switcher(key: Optional[str] = None) -> Switcher:
        """ Get a switcher by key """
        return Switcher(Client.context, key)
    

    @staticmethod
    def load_snapshot(options: Optional[LoadSnapshotOptions] = None) -> int:
        """ Load Domain from snapshot """
        snapshot_options = get(options, LoadSnapshotOptions())

        GlobalSnapshot.init(load_domain(
            get(Client.context.options.snapshot_location, ''),
            get(Client.context.environment, DEFAULT_ENVIRONMENT)
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
            context=Client.context,
            snapshot_version=Client.snapshot_version(),
        )

        if snapshot is not None:
            if Client.context.options.snapshot_location is not None:
                save_snapshot(
                    snapshot=snapshot, 
                    snapshot_location=get(Client.context.options.snapshot_location, ''), 
                    environment=get(Client.context.environment, DEFAULT_ENVIRONMENT)
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
            Client.context.options.snapshot_auto_update_interval = interval

        if Client.context.options.snapshot_auto_update_interval is not None and \
            Client.context.options.snapshot_auto_update_interval > 0:
            SnapshotAutoUpdater.schedule(
                interval=Client.context.options.snapshot_auto_update_interval,
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
    def _is_check_snapshot_available(fetch_remote = False) -> bool:
        return Client.snapshot_version() == 0 and (fetch_remote or not Client.context.options.local)