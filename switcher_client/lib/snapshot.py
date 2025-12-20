from enum import Enum
from typing import Optional
from unittest import case

class StrategiesType(Enum):
    VALUE = "VALUE_VALIDATION"
    NUMERIC = "NUMERIC_VALIDATION"

class OperationsType(Enum):
    EXIST = "EXIST"
    NOT_EXIST = "NOT_EXIST"
    EQUAL = "EQUAL"
    NOT_EQUAL = "NOT_EQUAL"
    GREATER = "GREATER"
    LOWER = "LOWER"
    BETWEEN = "BETWEEN"

def process_operation(strategy_config: dict, input_value: str) -> Optional[bool]:
    strategy = strategy_config.get('strategy')
    operation = strategy_config.get('operation', '')
    values = strategy_config.get('values', [])
    
    match strategy:
        case StrategiesType.VALUE.value:
            return process_value(operation, values, input_value)
        case StrategiesType.NUMERIC.value:
            return process_numeric(operation, values, input_value)
            
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
        
def process_numeric(operation: str, values: list, input_value: str) -> Optional[bool]:
    try:
        numeric_input = float(input_value)
    except ValueError:
        return None
    
    numeric_values = [float(v) for v in values]
    
    match operation:
        case OperationsType.EXIST.value:
            return numeric_input in numeric_values
        case OperationsType.NOT_EXIST.value:
            return numeric_input not in numeric_values
        case OperationsType.EQUAL.value:
            return numeric_input in numeric_values
        case OperationsType.NOT_EQUAL.value:
            return numeric_input not in numeric_values
        case OperationsType.GREATER.value:
            return any(numeric_input > v for v in numeric_values)
        case OperationsType.LOWER.value:
            return any(numeric_input < v for v in numeric_values)
        case OperationsType.BETWEEN.value:
            return numeric_input >= numeric_values[0] and numeric_input <= numeric_values[1]
