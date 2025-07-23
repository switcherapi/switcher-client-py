from abc import ABCMeta
from typing import Optional, Self

# Strategy types
VALUE_VALIDATION = 'VALUE_VALIDATION'

class SwitcherData(metaclass=ABCMeta):
    def __init__(self, key: Optional[str] = None):
        self._key = key
        self._input = []
        self._show_details = False

    def check(self, strategy_type: str, input: str)-> Self:
        """ Adds a strategy for validation """
        self._input = [item for item in self._input if item[0] != strategy_type]
        self._input.append([strategy_type, input])
        return self

    def check_value(self, input: str) -> Self:
        """ Adds VALUE_VALIDATION input for strategy validation """
        return self.check(VALUE_VALIDATION, input)