DEFAULT_ENVIRONMENT = 'default'
DEFAULT_LOCAL = False

class ContextOptions:
    def __init__(self, local = DEFAULT_LOCAL, snapshot_location = None):
        self.local = local
        self.snapshot_location = snapshot_location

class Context:
    def __init__(self, domain, url, api_key, component, environment, options = ContextOptions()):
        self.domain = domain
        self.url = url
        self.api_key = api_key
        self.component = component
        self.environment = environment
        self.options = options