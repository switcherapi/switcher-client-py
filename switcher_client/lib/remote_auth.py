from switcher_client.lib.remote import Remote
from switcher_client.lib.globals.global_context import Context
from switcher_client.lib.globals import GlobalAuth

class RemoteAuth:
    __context: Context = Context.empty()

    @staticmethod
    def init(context: Context):
        RemoteAuth.__context = context
        GlobalAuth.init(context.url)

    @staticmethod
    def auth():
        token, exp = Remote.auth(RemoteAuth.__context)
        GlobalAuth.set_token(token)
        GlobalAuth.set_exp(exp)