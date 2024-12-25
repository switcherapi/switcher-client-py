from typing import Optional

from switcher_client.context import Context, ContextOptions
from switcher_client.context import DEFAULT_ENVIRONMENT

class Client:
    context: Optional[Context] = None

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

    @staticmethod
    def clear_context():
        Client.context = None

    @staticmethod
    def verify_context():
        if not Client.context:
            raise ValueError('Context is not set')