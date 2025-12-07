from .execution_logger import ExecutionLogger

def get(value, default_value):
    """ Return value if not None, otherwise return default_value """
    return value if value is not None else default_value

__all__ = [
    'ExecutionLogger',
    'get',
]
