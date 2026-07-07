from dataclasses import dataclass
from typing import Optional

DEFAULT_ENVIRONMENT = 'default'
DEFAULT_LOCAL = False
DEFAULT_LOGGER = False
DEFAULT_FREEZE = False
DEFAULT_RESTRICT_RELAY = True
DEFAULT_REGEX_MAX_BLACKLISTED = 100
DEFAULT_REGEX_MAX_TIME_LIMIT = 3000
DEFAULT_REMOTE_CONNECT_TIMEOUT = 0.3
DEFAULT_REMOTE_READ_TIMEOUT = 5.0
DEFAULT_REMOTE_WRITE_TIMEOUT = 5.0
DEFAULT_REMOTE_POOL_TIMEOUT = 5.0
DEFAULT_REMOTE_MAX_KEEPALIVE_CONNECTIONS = 20
DEFAULT_REMOTE_MAX_CONNECTIONS = 100
DEFAULT_REMOTE_KEEPALIVE_EXPIRY = 30.0
DEFAULT_REMOTE_CERT_PATH = None
DEFAULT_REMOTE_AUTO_RENEW_TOKEN = False
DEFAULT_TEST_MODE = False

@dataclass
class RemoteOptions:
    """
    :param cert_path: The path to the SSL certificate file for secure connections.
        If not set, it will use the default system certificates
    :param auto_renew_token: When enabled, it will automatically renew the token before it expires.
    :param connect_timeout: Max time in seconds to establish a remote connection.
        Lower values help silent mode trip faster when the upstream is unavailable
    :param read_timeout: Max time in seconds to wait for a remote response body
    :param write_timeout: Max time in seconds to send a remote request body
    :param pool_timeout: Max time in seconds to wait for a pooled connection
    :param max_keepalive_connections: Max number of idle keep-alive connections to maintain
    :param max_connections: Max number of concurrent connections allowed
    :param keepalive_expiry: Max time in seconds a keep-alive connection can remain idle
    """
    # pylint: disable=too-many-instance-attributes
    cert_path: Optional[str] = DEFAULT_REMOTE_CERT_PATH
    auto_renew_token: bool = DEFAULT_REMOTE_AUTO_RENEW_TOKEN
    connect_timeout: float = DEFAULT_REMOTE_CONNECT_TIMEOUT
    read_timeout: float = DEFAULT_REMOTE_READ_TIMEOUT
    write_timeout: float = DEFAULT_REMOTE_WRITE_TIMEOUT
    pool_timeout: float = DEFAULT_REMOTE_POOL_TIMEOUT
    max_keepalive_connections: int = DEFAULT_REMOTE_MAX_KEEPALIVE_CONNECTIONS
    max_connections: int = DEFAULT_REMOTE_MAX_CONNECTIONS
    keepalive_expiry: float = DEFAULT_REMOTE_KEEPALIVE_EXPIRY

@dataclass
class ContextOptions:
    """
    :param local: When enabled it will use the local snapshot (file or in-memory).
        If not set, it will use the remote API
    :param logger: When enabled it allows inspecting the result details with
        Client.get_execution(switcher). If not set, it will not log the result details
    :param freeze: This option prevents the execution of background cache update when
        using throttle. Use Client.clear_logger() to reset the in-memory cache if
        snapshot are renewed
    :param snapshot_location: The location of the snapshot file.
        If not set, it will use the in-memory snapshot
    :param snapshot_auto_update_interval: The interval in seconds to auto-update
        the snapshot. If not set, it will not auto-update the snapshot
    :param silent_mode: When defined it will switch to local during the specified time
        before it switches back to remote, e.g. 5s (s: seconds - m: minutes - h: hours)
    :param throttle_max_workers: The maximum number of workers to use for background
        refresh when throttle is enabled. If None, the default value is based on the
        number of CPUs. Default is None
    :param regex_max_black_list: The maximum number of blacklisted regex inputs.
        If not set, it will use the default value of 100
    :param regex_max_time_limit: The maximum time limit in milliseconds for regex
        matching. If not set, it will use the default value of 3000 ms
    :param restrict_relay: When enabled it will restrict the use of relay when local
        is enabled. Default is True
    :param remote: Remote transport settings such as certificate path, connect/read/write/pool timeouts
    """
    # pylint: disable=too-many-arguments, too-many-instance-attributes
    def __init__(self, *,
                local: bool = DEFAULT_LOCAL,
                logger: bool = DEFAULT_LOGGER,
                freeze: bool = DEFAULT_FREEZE,
                regex_max_black_list: int = DEFAULT_REGEX_MAX_BLACKLISTED,
                regex_max_time_limit: int = DEFAULT_REGEX_MAX_TIME_LIMIT,
                restrict_relay: bool = DEFAULT_RESTRICT_RELAY,
                snapshot_location: Optional[str] = None,
                snapshot_auto_update_interval: Optional[int] = None,
                silent_mode: Optional[str] = None,
                throttle_max_workers: Optional[int] = None,
                remote: Optional[RemoteOptions] = None):
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
        self.remote = remote or RemoteOptions()

@dataclass
class Context:
    """
    :param domain: Your Switcher domain name
    :param url: Switcher-API endpoint URL.
    :param api_key: The API key for authentication
    :param component: Your application identifier
    :param environment: Target environment name. If not set, it will use the default environment
    :param options: The context options
    """
    # pylint: disable=too-many-arguments
    def __init__(self, *,
                 domain: Optional[str], url: Optional[str], api_key: Optional[str], component: Optional[str],
                 environment: Optional[str], options: Optional[ContextOptions] = None):
        self.domain = domain
        self.url = url
        self.api_key = api_key
        self.component = component
        self.environment = environment
        self.options = ContextOptions() if options is None else options

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
