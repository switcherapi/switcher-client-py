from datetime import datetime
from abc import ABCMeta
from typing import Optional, Self

# Strategy types
VALUE_VALIDATION = 'VALUE_VALIDATION'

class SwitcherData(metaclass=ABCMeta):
    def __init__(self, key: Optional[str] = None):
        self._key = key
        self._input = []
        self._show_details = False
        self._throttle_period = 0
        self._next_refresh_time = 0 # timestamp

    def check(self, strategy_type: str, input: str)-> Self:
        """ Adds a strategy for validation """
        self._input = [item for item in self._input if item[0] != strategy_type]
        self._input.append([strategy_type, input])
        return self

    def check_value(self, input: str) -> Self:
        """ Adds VALUE_VALIDATION input for strategy validation """
        return self.check(VALUE_VALIDATION, input)
    
    def throttle(self, period: int) -> Self:
        """ Sets throttle period in milliseconds """
        self._throttle_period = period

        if self._next_refresh_time == 0:
            self._next_refresh_time = int(datetime.now().timestamp() * 1000) + period

        return self