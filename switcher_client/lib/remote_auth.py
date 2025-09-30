from time import time

from switcher_client.lib.remote import Remote
from switcher_client.lib.globals.global_context import Context
from switcher_client.lib.globals import GlobalAuth

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