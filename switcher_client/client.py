from typing import Optional

from switcher_client.lib.globals.global_snapshot import GlobalSnapshot, LoadSnapshotOptions
from switcher_client.lib.remote_auth import RemoteAuth
from switcher_client.lib.globals.global_context import Context, ContextOptions
from switcher_client.lib.globals.global_context import DEFAULT_ENVIRONMENT
from switcher_client.lib.snapshot_loader import load_domain, validate_snapshot
from switcher_client.lib.utils import get
from switcher_client.switcher import Switcher

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

        # Initialize Auth
        RemoteAuth.init(Client.context)

    @staticmethod
    def clear_context():
        Client.context = Context.empty()

    @staticmethod
    def verify_context():
        required_fields = [
            Client.context.domain,
            Client.context.url,
            Client.context.api_key,
            Client.context.component
        ]

        if any(field is None or field == '' for field in required_fields):
            raise ValueError('Context is not set')

    @staticmethod
    def get_switcher(key: Optional[str] = None) -> Switcher:
        """ Get a switcher by key """
        Client.verify_context()
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
            GlobalSnapshot.init(snapshot)
            return True
        
        return False

    @staticmethod
    def snapshot_version() -> int:
        """ Get the version of the snapshot """
        snapshot = GlobalSnapshot.snapshot()

        if snapshot is None:
            return 0
        
        return snapshot.data.domain.version
    
    @staticmethod
    def _is_check_snapshot_available(fetch_remote = False) -> bool:
        return Client.snapshot_version() == 0 and (fetch_remote or not Client.context.options.local)