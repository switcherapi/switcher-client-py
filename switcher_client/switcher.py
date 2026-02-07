from typing import Optional

from .lib.globals.global_context import Context
from .lib.globals.global_snapshot import GlobalSnapshot
from .lib.remote_auth import RemoteAuth
from .lib.globals import GlobalAuth
from .lib.remote import Remote
from .lib.resolver import Resolver
from .lib.types import ResultDetail
from .lib.utils.execution_logger import ExecutionLogger
from .switcher_data import SwitcherData

class Switcher(SwitcherData):
    def __init__(self, context: Context, key: Optional[str] = None):
        super().__init__(key) 
        self._context = context
        self._validate_args(key)

    def prepare(self, key: Optional[str] = None):
        """ Checks API credentials and connectivity """
        self._validate_args(key)
        RemoteAuth.auth()

    def is_on(self, key: Optional[str] = None) -> bool:
        """ Execute criteria """
        self._show_details = False
        self._validate_args(key, details=False)
        return self._submit().result
    
    def is_on_with_details(self, key: Optional[str] = None) -> ResultDetail:
        """ Execute criteria with details """
        self._validate_args(key, details=True)
        return self._submit()
    
    def _submit(self) -> ResultDetail:
        """ Submit criteria for execution (local or remote) """
        if (self._context.options.local):
            return self._execute_local_criteria()

        try:
            self.validate()
            if GlobalAuth.get_token() == 'SILENT':
                return self._execute_local_criteria()

            return self._execute_remote_criteria()
        except Exception as e:
            if self._context.options.silent_mode:
                RemoteAuth.update_silent_token()
                return self._execute_local_criteria()

            raise e
    
    def validate(self) -> 'Switcher':
        """ Validates client settings for remote API calls """
        errors = []

        RemoteAuth.is_valid()
        
        if not self._key:
            errors.append('Missing key field')

        self._execute_api_checks()
        if not GlobalAuth.get_token():
            errors.append('Missing token field')

        if errors:
            raise ValueError(f"Something went wrong: {', '.join(errors)}")
        
        return self

    def _validate_args(self, key: Optional[str] = None, details: Optional[bool] = None):
        if key is not None:
            self._key = key

        if details is not None:
            self._show_details = details

    def _execute_api_checks(self):
        """ Assure API is available and token is valid """
        RemoteAuth.check_health()
        if RemoteAuth.is_token_expired():
            self.prepare(self._key)

    def _execute_remote_criteria(self):
        """ Execute remote criteria """
        token = GlobalAuth.get_token()
        response = Remote.check_criteria(token, self._context, self)

        if self._can_log():
            ExecutionLogger.add(response, self._key, self._input)

        return response
    
    def _execute_local_criteria(self):
        """ Execute local criteria """
        return Resolver.check_criteria(GlobalSnapshot.snapshot(), self)
    
    def _can_log(self) -> bool:
        """ Check if logging is enabled """
        return self._context.options.logger and self._key is not None