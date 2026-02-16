from typing import Optional

DEFAULT_ENVIRONMENT = 'default'
DEFAULT_LOCAL = False
DEFAULT_LOGGER = False
DEFAULT_FREEZE = False

class ContextOptions:
    """
    :param local: When enabled it will use the local snapshot (file or in-memory). If not set, it will use the remote API
    :param logger: When enabled it allows inspecting the result details with Client.get_execution(switcher). If not set, it will not log the result details
    :param freeze: This option prevents the execution of background cache update when using throttle. Use Client.clear_logger() to reset the in-memory cache if snapshot are renewed
    :param snapshot_location: The location of the snapshot file. If not set, it will use the in-memory snapshot
    :param snapshot_auto_update_interval: The interval in milliseconds to auto-update the snapshot. If not set, it will not auto-update the snapshot
    :param silent_mode: When defined it will switch to local during the specified time before it switches back to remote, e.g. 5s (s: seconds - m: minutes - h: hours)
    :param throttle_max_workers: The maximum number of workers to use for background refresh when throttle is enabled. If None, the default value is based on the number of CPUs. Default is None
    """

    def __init__(self, 
                 local = DEFAULT_LOCAL,
                 logger = DEFAULT_LOGGER,
                 freeze = DEFAULT_FREEZE,
                 snapshot_location: Optional[str] = None, 
                 snapshot_auto_update_interval: Optional[int] = None,
                 silent_mode: Optional[str] = None,
                 throttle_max_workers: Optional[int] = None):
        self.local = local
        self.logger = logger
        self.freeze = freeze
        self.snapshot_location = snapshot_location
        self.snapshot_auto_update_interval = snapshot_auto_update_interval
        self.silent_mode = silent_mode
        self.throttle_max_workers = throttle_max_workers

class Context:
    def __init__(self, 
                 domain: Optional[str], url: Optional[str], api_key: Optional[str], component: Optional[str], 
                 environment: Optional[str], options: ContextOptions = ContextOptions()):
        self.domain = domain
        self.url = url
        self.api_key = api_key
        self.component = component
        self.environment = environment
        self.options = options
    
    @classmethod
    def empty(cls):
        return cls(
            domain='',
            url='',
            api_key='',
            component='',
            environment=DEFAULT_ENVIRONMENT,
            options=ContextOptions()
        )