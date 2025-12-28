from time import time

from .remote import Remote
from .globals.global_context import Context
from .globals import GlobalAuth

class RemoteAuth:
    __context: Context = Context.empty()

    @staticmethod
    def init(context: Context):
        RemoteAuth.__context = context
        GlobalAuth.init()

    @staticmethod
    def auth():
        token, exp = Remote.auth(RemoteAuth.__context)
        GlobalAuth.set_token(token)
        GlobalAuth.set_exp(exp)

    @staticmethod
    def check_health():
        if GlobalAuth.get_token() != 'SILENT':
            return
    
    @staticmethod
    def is_token_expired() -> bool:
        exp = GlobalAuth.get_exp()
        if exp is None:
            return True
        
        return float(exp) < time()
    
    @staticmethod
    def is_valid():
        required_fields = [
            ('url', RemoteAuth.__context.url),
            ('component', RemoteAuth.__context.component),
            ('api_key', RemoteAuth.__context.api_key),
        ]

        errors = [name for name, value in required_fields if not value]
        if errors:
            raise ValueError(f"Something went wrong: Missing or empty required fields ({', '.join(errors)})")
