import re

from enum import Enum
from typing import Optional
from datetime import datetime

from ..lib.types import StrategyConfig
from .utils.payload_reader import parse_json, payload_reader
from .utils.ipcidr import IPCIDR
from .utils.timed_match import TimedMatch

class StrategiesType(Enum):
    VALUE = "VALUE_VALIDATION"
    NUMERIC = "NUMERIC_VALIDATION"
    DATE = "DATE_VALIDATION"
    TIME = "TIME_VALIDATION"
    PAYLOAD = "PAYLOAD_VALIDATION"
    NETWORK = "NETWORK_VALIDATION"
    REGEX = "REGEX_VALIDATION"

class OperationsType(Enum):
    EXIST = "EXIST"
    NOT_EXIST = "NOT_EXIST"
    EQUAL = "EQUAL"
    NOT_EQUAL = "NOT_EQUAL"
    GREATER = "GREATER"
    LOWER = "LOWER"
    BETWEEN = "BETWEEN"
    HAS_ONE = "HAS_ONE"
    HAS_ALL = "HAS_ALL"

def process_operation(strategy_config: StrategyConfig, input_value: str) -> Optional[bool]:
    """Process the operation based on strategy configuration and input value."""

    strategy = strategy_config.strategy
    operation = strategy_config.operation
    values = strategy_config.values
    
    match strategy:
        case StrategiesType.VALUE.value:
            return _process_value(operation, values, input_value)
        case StrategiesType.NUMERIC.value:
            return _process_numeric(operation, values, input_value)
        case StrategiesType.DATE.value:
            return _process_date(operation, values, input_value)
        case StrategiesType.TIME.value:
            return _process_time(operation, values, input_value)
        case StrategiesType.PAYLOAD.value:
            return _process_payload(operation, values, input_value)
        case StrategiesType.NETWORK.value:
            return _process_network(operation, values, input_value)
        case StrategiesType.REGEX.value:
            return _process_regex(operation, values, input_value)
            
def _process_value(operation: str, values: list, input_value: str) -> Optional[bool]:
    """ Process VALUE strategy operations."""

    match operation:
        case OperationsType.EXIST.value:
            return input_value in values
        case OperationsType.NOT_EXIST.value:
            return input_value not in values
        case OperationsType.EQUAL.value:
            return input_value in values
        case OperationsType.NOT_EQUAL.value:
            return input_value not in values
        
def _process_numeric(operation: str, values: list, input_value: str) -> Optional[bool]:
    """ Process NUMERIC strategy operations."""

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

def _process_date(operation: str, values: list, input_value: str) -> Optional[bool]:
    """ Process DATE strategy operations."""

    try:
        date_input = _parse_datetime(input_value)
        date_values = [_parse_datetime(v) for v in values]
    except ValueError:
        return None

    match operation:
        case OperationsType.LOWER.value:
            return any(date_input <= v for v in date_values)
        case OperationsType.GREATER.value:
            return any(date_input >= v for v in date_values)
        case OperationsType.BETWEEN.value:
            return date_values[0] <= date_input <= date_values[1]
        
def _process_time(operation: str, values: list, input_value: str) -> Optional[bool]:
    """ Process TIME strategy operations."""

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
        
def _process_payload(operation: str, values: list, input_value: str) -> Optional[bool]:
    """ Process PAYLOAD strategy operations."""

    input_json = parse_json(input_value)
    if input_json is None:
        return False
    
    keys = payload_reader(input_json)
    
    match operation:
        case OperationsType.HAS_ONE.value:
            return any(value in keys for value in values)
        case OperationsType.HAS_ALL.value:
            return all(value in keys for value in values)

def _process_network(operation: str, values: list, input_value: str) -> Optional[bool]:
    """Process NETWORK strategy operations."""

    cidr_regex = re.compile(r'^(\d{1,3}\.){3}\d{1,3}(\/(\d|[1-2]\d|3[0-2]))$')
    
    match operation:
        case OperationsType.EXIST.value:
            return _process_network_exist(input_value, values, cidr_regex)
        case OperationsType.NOT_EXIST.value:
            return _process_network_not_exist(input_value, values, cidr_regex)
    
    return False

def _process_network_exist(input_value: str, values: list, cidr_regex) -> bool:
    """Check if input IP exists in any of the network ranges/IPs."""

    for value in values:
        if cidr_regex.match(value):
            cidr = IPCIDR(value)
            if cidr.is_ip4_in_cidr(input_value):
                return True
        else:
            if input_value in values:
                return True
                
    return False

def _process_network_not_exist(input_value: str, values: list, cidr_regex) -> bool:
    """Check if input IP does not exist in any of the network ranges/IPs."""

    result = []
    for element in values:
        if cidr_regex.match(element):
            cidr = IPCIDR(element)
            if cidr.is_ip4_in_cidr(input_value):
                result.append(element)
        else:
            if input_value in values:
                result.append(element)
    
    return len(result) == 0

def _process_regex(operation: str, values: list, input_value: str) -> Optional[bool]:
    """ Process REGEX strategy operations with timeout protection."""

    match operation:
        case OperationsType.EXIST.value:
            return TimedMatch.try_match(values, input_value, use_fullmatch=False)
        case OperationsType.NOT_EXIST.value:
            result = TimedMatch.try_match(values, input_value, use_fullmatch=False)
            return not result
        case OperationsType.EQUAL.value:
            return TimedMatch.try_match(values, input_value, use_fullmatch=True)
        case OperationsType.NOT_EQUAL.value:
            result = TimedMatch.try_match(values, input_value, use_fullmatch=True)
            return not result
        
def _parse_datetime(date_str: str):
    """Parse datetime string that can be either date-only or datetime format."""

    formats = ['%Y-%m-%dT%H:%M', '%Y-%m-%d']
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
        
    raise ValueError(f"Unable to parse date: {date_str}")