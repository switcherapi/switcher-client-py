from typing import Optional

from switcher_client.errors import RemoteAuthError
from switcher_client.lib.remote import Remote
from switcher_client.context import Context

class RemoteAuth:
    __context: Optional[Context] = None
    __token = None
    __exp = None

    @staticmethod
    def init(context: Context):
        RemoteAuth.__context = context
        RemoteAuth.__token = None
        RemoteAuth.__exp = None

    @staticmethod
    def auth():
        token, exp = Remote.auth(RemoteAuth.__context)
        RemoteAuth.__token = token
        RemoteAuth.__exp = exp

    @staticmethod
    def get_token():
        return RemoteAuth.__token

    @staticmethod
    def get_exp():
        return RemoteAuth.__exp