from typing import Optional

from switcher_client.lib.types import Entry
from .execution_logger import ExecutionLogger

def get(value, default_value):
    """ Return value if not None, otherwise return default_value """
    return value if value is not None else default_value

def get_entry(input: list) -> list[Entry]:
    """ Prepare entry dictionary from input strategy handling """
    entry: list[Entry] = []
    for strategy_type, input_value in input:
        entry.append(Entry(strategy_type, input_value))
    
    return entry

__all__ = [
    'ExecutionLogger',
    'get_entry',
    'get',
]
