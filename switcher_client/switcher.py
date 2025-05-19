from typing import Optional

from switcher_client.lib.globals.global_context import Context
from switcher_client.lib.remote_auth import RemoteAuth
from switcher_client.lib.globals import GlobalAuth
from switcher_client.lib.remote import Remote

class Switcher:
    def __init__(self, context: Context, key: Optional[str] = None):
        self.context = context
        self.key = key
        self.input = {}
        self.show_details = False

    def is_on(self, key: Optional[str] = None) -> bool:
        """ Execute criteria """
        result = False

        self.__validate_args(key)
        self.__execute_api_checks()
        result = self.__execute_remote_criteria()

        return result

    def __validate_args(self, key: Optional[str] = None):
        if self.key is None:
            self.key = key

        if self.key is None:
            raise ValueError('Key is required')

    def __execute_api_checks(self):
        """ Assure API is available and token is valid """
        RemoteAuth.auth()

    def __execute_remote_criteria(self):
        """ Execute remote criteria """
        token = GlobalAuth.get_token()
        GlobalAuth.get_exp()

        response_criteria = Remote.check_criteria(token, self.context, self.key, self.input, self.show_details)
        return response_criteria.result