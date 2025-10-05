from typing import Optional, Callable

from switcher_client.lib.globals.global_snapshot import GlobalSnapshot, LoadSnapshotOptions
from switcher_client.lib.remote_auth import RemoteAuth
from switcher_client.lib.globals.global_context import Context, ContextOptions
from switcher_client.lib.globals.global_context import DEFAULT_ENVIRONMENT
from switcher_client.lib.snapshot_auto_updater import SnapshotAutoUpdater
from switcher_client.lib.snapshot_loader import load_domain, validate_snapshot, save_snapshot
from switcher_client.lib.utils import get
from switcher_client.switcher import Switcher

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
            Client.__build_options(options)

        # Initialize Auth
        RemoteAuth.init(Client.context)

    @staticmethod
    def __build_options(options: ContextOptions):
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

        if Client.__is_check_snapshot_available(snapshot_options.fetch_remote):
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
    def __is_check_snapshot_available(fetch_remote = False) -> bool:
        return Client.snapshot_version() == 0 and (fetch_remote or not Client.context.options.local)