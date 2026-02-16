from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
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
        super().__init__(context, key) 
        self._context = context
        self._init_worker(context)
        self._validate_args(key)

    def _init_worker(self, context: Context):
        self._background_executor = ThreadPoolExecutor(
            max_workers=context.options.throttle_max_workers,
            thread_name_prefix="SwitcherBackgroundRefresh"
        )

    def prepare(self, key: Optional[str] = None):
        """ Checks API credentials and connectivity """
        self._validate_args(key)
        RemoteAuth.auth()

    def is_on(self, key: Optional[str] = None) -> bool:
        """ Execute criteria """
        self._show_details = False
        self._validate_args(key, details=False)

        # try get cached result
        cached_result = self._try_cached_result()
        if cached_result is not None:
            return cached_result.result
        
        return self._submit().result
    
    def is_on_with_details(self, key: Optional[str] = None) -> ResultDetail:
        """ Execute criteria with details """
        self._validate_args(key, details=True)

        # try get cached result
        cached_result = self._try_cached_result()
        if cached_result is not None:
            return cached_result
        
        return self._submit()
    
    def schedule_background_refresh(self):
        """ Schedules background refresh of the last criteria request """
        now = int(datetime.now().timestamp() * 1000)
        
        if now > self._next_refresh_time:
            self._next_refresh_time = now + self._throttle_period
            self._background_executor.submit(self._submit)
    
    def _submit(self) -> ResultDetail:
        """ Submit criteria for execution (local or remote) """
        # verify if query from snapshot
        if (self._context.options.local):
            return self._execute_local_criteria()

        try:
            self.validate()
            if GlobalAuth.get_token() == 'SILENT':
                return self._execute_local_criteria()

            return self._execute_remote_criteria()
        except Exception as e:
            self._notify_error(e)
            
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

    def _try_cached_result(self) -> Optional[ResultDetail]:
        """ Try get cached result if throttle is enabled and criteria was recently executed """
        if self._has_throttle():
            if not self._context.options.freeze:
                self.schedule_background_refresh()

            cached_result_logger = ExecutionLogger.get_execution(self._key, self._input)
            if cached_result_logger.key is not None:
                return cached_result_logger.response
            
        return None

    def _notify_error(self, error: Exception):
        """ Notify asynchronous error to the subscribed callback """
        if ExecutionLogger._callback_error:
            ExecutionLogger._callback_error(error)

    def _execute_remote_criteria(self):
        """ Execute remote criteria """
        try:
            token = GlobalAuth.get_token()
            response = Remote.check_criteria(token, self._context, self)

            if self._can_log():
                ExecutionLogger.add(response, self._key, self._input)

            return response
        except Exception as e:
            return self._get_default_result_or_raise(e)
    
    def _execute_local_criteria(self):
        """ Execute local criteria """
        try:
            response = Resolver.check_criteria(GlobalSnapshot.snapshot(), self)
            if self._can_log():
                ExecutionLogger.add(response, self._key, self._input)

            return response
        except Exception as e:
            return self._get_default_result_or_raise(e)
    
    def _can_log(self) -> bool:
        """ Check if logging is enabled """
        return self._context.options.logger and self._key is not None
    
    def _has_throttle(self) -> bool:
        """ Check if throttle is enabled and criteria was recently executed """
        return self._throttle_period != 0
    
    def _get_default_result_or_raise(self, e) -> ResultDetail:
        """ Get default result if set, otherwise raise the error """
        if self._default_result is None:
            raise e
        
        self._notify_error(e)
        return ResultDetail.create(result=self._default_result, reason="Default result")