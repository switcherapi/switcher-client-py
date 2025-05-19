from typing import Optional

from switcher_client.lib.remote_auth import RemoteAuth
from switcher_client.lib.globals.global_context import Context, ContextOptions
from switcher_client.lib.globals.global_context import DEFAULT_ENVIRONMENT
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