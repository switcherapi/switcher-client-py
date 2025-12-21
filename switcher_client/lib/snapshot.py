from enum import Enum
from typing import Optional
from datetime import datetime

class StrategiesType(Enum):
    VALUE = "VALUE_VALIDATION"
    NUMERIC = "NUMERIC_VALIDATION"
    DATE = "DATE_VALIDATION"
    TIME = "TIME_VALIDATION"

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
            return __process_value(operation, values, input_value)
        case StrategiesType.NUMERIC.value:
            return __process_numeric(operation, values, input_value)
        case StrategiesType.DATE.value:
            return __process_date(operation, values, input_value)
        case StrategiesType.TIME.value:
            return __process_time(operation, values, input_value)
            
def __process_value(operation: str, values: list, input_value: str) -> Optional[bool]:
    match operation:
        case OperationsType.EXIST.value:
            return input_value in values
        case OperationsType.NOT_EXIST.value:
            return input_value not in values
        case OperationsType.EQUAL.value:
            return input_value in values
        case OperationsType.NOT_EQUAL.value:
            return input_value not in values
        
def __process_numeric(operation: str, values: list, input_value: str) -> Optional[bool]:
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

def __process_date(operation: str, values: list, input_value: str) -> Optional[bool]:
    try:
        date_input = __parse_datetime(input_value)
        date_values = [__parse_datetime(v) for v in values]
    except ValueError:
        return None

    match operation:
        case OperationsType.LOWER.value:
            return any(date_input <= v for v in date_values)
        case OperationsType.GREATER.value:
            return any(date_input >= v for v in date_values)
        case OperationsType.BETWEEN.value:
            return date_values[0] <= date_input <= date_values[1]
        
def __process_time(operation: str, values: list, input_value: str) -> Optional[bool]:
    try:
        time_input = datetime.strptime(input_value, '%H:%M').time()
        time_values = [datetime.strptime(v, '%H:%M').time() for v in values]
    except ValueError:
        return None

    match operation:
        case OperationsType.LOWER.value:
            return any(time_input <= v for v in time_values)
        case OperationsType.GREATER.value:
            return any(time_input >= v for v in time_values)
        case OperationsType.BETWEEN.value:
            return time_values[0] <= time_input <= time_values[1]
        
def __parse_datetime(date_str: str):
    """Parse datetime string that can be either date-only or datetime format."""

    formats = ['%Y-%m-%dT%H:%M', '%Y-%m-%d']
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
        
    raise ValueError(f"Unable to parse date: {date_str}")