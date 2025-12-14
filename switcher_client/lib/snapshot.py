from enum import Enum
from typing import Optional
from unittest import case

class StrategiesType(Enum):
    VALUE = "VALUE_VALIDATION"

class OperationsType(Enum):
    EXIST = "EXIST"
    NOT_EXIST = "NOT_EXIST"
    EQUAL = "EQUAL"
    NOT_EQUAL = "NOT_EQUAL"

def process_operation(strategy_config: dict, input_value: str) -> Optional[bool]:
    strategy = strategy_config.get('strategy')
    operation = strategy_config.get('operation', '')
    values = strategy_config.get('values', [])
    
    match strategy:
        case StrategiesType.VALUE.value:
            return process_value(operation, values, input_value)
            
def process_value(operation: str, values: list, input_value: str) -> Optional[bool]:
    match operation:
        case OperationsType.EXIST.value:
            return input_value in values
        case OperationsType.NOT_EXIST.value:
            return input_value not in values
        case OperationsType.EQUAL.value:
            return input_value in values
        case OperationsType.NOT_EQUAL.value:
            return input_value not in values