from typing import Optional

DEFAULT_ENVIRONMENT = 'default'
DEFAULT_LOCAL = False

class ContextOptions:
    def __init__(self, 
                 local = DEFAULT_LOCAL,
                 logger = False,
                 snapshot_location: Optional[str] = None, 
                 snapshot_auto_update_interval: Optional[int] = None,
                 silent_mode: Optional[str] = None,
                 throttle_max_workers: Optional[int] = None):
        self.local = local
        self.logger = logger
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