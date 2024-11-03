from switcher_client.context import Context
from switcher_client.context import DEFAULT_ENVIRONMENT

class Client:
    context = None

    @staticmethod
    def build_context(
        domain: str, 
        url: str,
        api_key: str,
        component: str,
        environment: str | None = DEFAULT_ENVIRONMENT):
        """ 
        Build the context for the client 

        :param domain: Domain name
        :param url:Switcher-API URL
        :param api_key: Switcher-API key generated for the application/component
        :param component: Application/component name
        :param environment: Environment name
            
        """
        Client.context = Context(domain, url, api_key, component, environment)

    @staticmethod
    def clear_context():
        Client.context = None

    @staticmethod
    def verify_context():
        if not Client.context:
            raise ValueError('Context is not set')