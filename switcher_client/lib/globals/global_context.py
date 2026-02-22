from typing import Optional

DEFAULT_ENVIRONMENT = 'default'
DEFAULT_LOCAL = False
DEFAULT_LOGGER = False
DEFAULT_FREEZE = False
DEFAULT_RESTRICT_RELAY = True
DEFAULT_REGEX_MAX_BLACKLISTED = 100
DEFAULT_REGEX_MAX_TIME_LIMIT = 3000

class ContextOptions:
    """
    :param local: When enabled it will use the local snapshot (file or in-memory). If not set, it will use the remote API
    :param logger: When enabled it allows inspecting the result details with Client.get_execution(switcher). If not set, it will not log the result details
    :param freeze: This option prevents the execution of background cache update when using throttle. Use Client.clear_logger() to reset the in-memory cache if snapshot are renewed
    :param snapshot_location: The location of the snapshot file. If not set, it will use the in-memory snapshot
    :param snapshot_auto_update_interval: The interval in milliseconds to auto-update the snapshot. If not set, it will not auto-update the snapshot
    :param silent_mode: When defined it will switch to local during the specified time before it switches back to remote, e.g. 5s (s: seconds - m: minutes - h: hours)
    :param throttle_max_workers: The maximum number of workers to use for background refresh when throttle is enabled. If None, the default value is based on the number of CPUs. Default is None
    :param regex_max_black_list: The maximum number of blacklisted regex inputs. If not set, it will use the default value of 100
    :param regex_max_time_limit: The maximum time limit in milliseconds for regex matching. If not set, it will use the default value of 3000 ms
    :param restrict_relay: When enabled it will restrict the use of relay when local is enabled. Default is True
    """

    def __init__(self, 
                 local: bool = DEFAULT_LOCAL,
                 logger: bool = DEFAULT_LOGGER,
                 freeze: bool = DEFAULT_FREEZE,
                 regex_max_black_list: int = DEFAULT_REGEX_MAX_BLACKLISTED,
                 regex_max_time_limit: int = DEFAULT_REGEX_MAX_TIME_LIMIT,
                 restrict_relay: bool = DEFAULT_RESTRICT_RELAY,
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
        self.restrict_relay = restrict_relay
        self.throttle_max_workers = throttle_max_workers
        self.regex_max_black_list = regex_max_black_list
        self.regex_max_time_limit = regex_max_time_limit

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