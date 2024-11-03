DEFAULT_ENVIRONMENT = 'default'

class Context:
    def __init__(self, domain, url, api_key, component, environment):
        self.domain = domain
        self.url = url
        self.api_key = api_key
        self.component = component
        self.environment = environment