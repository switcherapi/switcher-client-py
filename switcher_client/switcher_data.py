from datetime import datetime
from abc import ABCMeta
from typing import Optional, Self, Union

from .lib.globals.global_context import Context
from .lib.snapshot import StrategiesType

class SwitcherData(metaclass=ABCMeta):
    def __init__(self, context: Context,key: Optional[str] = None):
        self._context = context
        self._key = key
        self._input = []
        self._show_details = False
        self._throttle_period = 0
        self._next_refresh_time = 0 # timestamp
        self._default_result = None

    def check(self, strategy_type: str, input: str)-> Self:
        """ Adds a strategy for validation """
        self._input = [item for item in self._input if item[0] != strategy_type]
        self._input.append([strategy_type, input])
        return self

    def check_value(self, input: str) -> Self:
        """ Adds VALUE_VALIDATION input for strategy validation """
        return self.check(StrategiesType.VALUE.value, input)
    
    def check_network(self, input: str) -> Self:
        """ Adds NETWORK_VALIDATION input for strategy validation """
        return self.check(StrategiesType.NETWORK.value, input)
    
    def check_regex(self, input: str) -> Self:
        """ Adds REGEX_VALIDATION input for strategy validation """
        return self.check(StrategiesType.REGEX.value, input)
    
    def check_payload(self, input: Union[str, dict]) -> Self:
        """ Adds PAYLOAD_VALIDATION input for strategy validation """
        if isinstance(input, dict):
            import json
            payload_str = json.dumps(input)
        else:
            payload_str = input
            
        return self.check(StrategiesType.PAYLOAD.value, payload_str)
    
    def throttle(self, period: int) -> Self:
        """ Sets throttle period in milliseconds """
        self._throttle_period = period

        if self._next_refresh_time == 0:
            self._next_refresh_time = int(datetime.now().timestamp() * 1000) + period

        if self._throttle_period > 0:
            self._context.options.logger = True

        return self
    
    def default_result(self, result: bool) -> Self:
        """ Sets the default result for the switcher """
        self._default_result = result
        return self