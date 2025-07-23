from typing import Optional

from switcher_client.lib.globals.global_context import Context
from switcher_client.lib.remote_auth import RemoteAuth
from switcher_client.lib.globals import GlobalAuth
from switcher_client.lib.remote import Remote
from switcher_client.switcher_data import SwitcherData

class Switcher(SwitcherData):
    def __init__(self, context: Context, key: Optional[str] = None):
        super().__init__(key) 
        self._context = context

    def is_on(self, key: Optional[str] = None) -> bool:
        """ Execute criteria """
        self.__validate_args(key)
        return self.__submit()
    
    def __submit(self) -> bool:
        """ Submit criteria for execution (local or remote) """

        self.__validate()
        self.__execute_api_checks()
        return self.__execute_remote_criteria()
    
    def __validate(self) -> 'Switcher':
        """ Validates client settings for remote API calls """
        errors = []

        if not self._key:
            errors.append('Missing key field')

        if errors:
            raise ValueError(f"Something went wrong: {', '.join(errors)}")
        
        return self

    def __validate_args(self, key: Optional[str] = None):
        if key is not None:
            self._key = key

    def __execute_api_checks(self):
        """ Assure API is available and token is valid """
        RemoteAuth.auth()

    def __execute_remote_criteria(self):
        """ Execute remote criteria """
        token = GlobalAuth.get_token()
        GlobalAuth.get_exp()

        response_criteria = Remote.check_criteria(token, self._context, self)
        return response_criteria.result