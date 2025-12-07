from typing import Optional

from switcher_client.lib.globals.global_context import Context
from switcher_client.lib.globals.global_snapshot import GlobalSnapshot
from switcher_client.lib.remote_auth import RemoteAuth
from switcher_client.lib.globals import GlobalAuth
from switcher_client.lib.remote import Remote
from switcher_client.lib.resolver import Resolver
from switcher_client.lib.types import ResultDetail
from switcher_client.lib.utils.execution_logger import ExecutionLogger
from switcher_client.switcher_data import SwitcherData

class Switcher(SwitcherData):
    def __init__(self, context: Context, key: Optional[str] = None):
        super().__init__(key) 
        self._context = context
        self.__validate_args(key)

    def prepare(self, key: Optional[str] = None):
        """ Checks API credentials and connectivity """
        self.__validate_args(key)
        RemoteAuth.auth()

    def is_on(self, key: Optional[str] = None) -> bool:
        """ Execute criteria """
        self._show_details = False
        self.__validate_args(key, details=False)
        return self.__submit().result
    
    def is_on_with_details(self, key: Optional[str] = None) -> ResultDetail:
        """ Execute criteria with details """
        self.__validate_args(key, details=True)
        return self.__submit()
    
    def __submit(self) -> ResultDetail:
        """ Submit criteria for execution (local or remote) """
        if (self._context.options.local):
            return self.__execute_local_criteria()

        self.validate()
        response = self.__execute_remote_criteria()

        return response
    
    def validate(self) -> 'Switcher':
        """ Validates client settings for remote API calls """
        errors = []

        RemoteAuth.is_valid()
        
        if not self._key:
            errors.append('Missing key field')

        self.__execute_api_checks()
        if not GlobalAuth.get_token():
            errors.append('Missing token field')

        if errors:
            raise ValueError(f"Something went wrong: {', '.join(errors)}")
        
        return self

    def __validate_args(self, key: Optional[str] = None, details: Optional[bool] = None):
        if key is not None:
            self._key = key

        if details is not None:
            self._show_details = details

    def __execute_api_checks(self):
        """ Assure API is available and token is valid """
        RemoteAuth.check_health()
        if RemoteAuth.is_token_expired():
            self.prepare(self._key)

    def __execute_remote_criteria(self):
        """ Execute remote criteria """
        token = GlobalAuth.get_token()
        response = Remote.check_criteria(token, self._context, self)

        if self.__can_log():
            ExecutionLogger.add(response, self._key, self._input)

        return response
    
    def __execute_local_criteria(self):
        """ Execute local criteria """
        return Resolver.check_criteria(GlobalSnapshot.snapshot(), self)
    
    def __can_log(self) -> bool:
        """ Check if logging is enabled """
        return self._context.options.logger and self._key is not None