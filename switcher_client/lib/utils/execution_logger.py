from typing import Optional, Callable, List

from ...lib.types import ResultDetail

# Global logger storage
_logger: List['ExecutionLogger'] = []

class ExecutionLogger:
    """It keeps track of latest execution results."""
    
    _callback_error: Optional[Callable[[Exception], None]] = None
    
    def __init__(self):
        self.key: Optional[str] = None
        self.input: Optional[List[List[str]]] = None
        self.response: ResultDetail = ResultDetail(result=False, reason=None, metadata=None)
    
    @staticmethod
    def add(response: ResultDetail, key: str, input: Optional[List[List[str]]] = None) -> None:
        """Add new execution result"""
        global _logger
        
        # Remove existing execution with same key and input
        for index in range(len(_logger)):
            log = _logger[index]
            if ExecutionLogger._has_execution(log, key, input):
                _logger.pop(index)
                break
        
        # Create new execution log entry
        new_log = ExecutionLogger()
        new_log.key = key
        new_log.input = input
        new_log.response = ResultDetail(
            result=response.result,
            reason=response.reason,
            metadata={**(response.metadata or {}), 'cached': True}
        )
        
        _logger.append(new_log)
    
    @staticmethod
    def get_execution(key: str, input: Optional[List[List[str]]] = None) -> 'ExecutionLogger':
        """Retrieve a specific result given a key and an input"""
        global _logger
        
        for log in _logger:
            if ExecutionLogger._has_execution(log, key, input):
                return log
        
        return ExecutionLogger()
    
    @staticmethod
    def get_by_key(key: str) -> List['ExecutionLogger']:
        """Retrieve results given a switcher key"""
        global _logger
        
        return [log for log in _logger if log.key == key]
    
    @staticmethod
    def clear_logger() -> None:
        """Clear all results"""
        global _logger
        _logger.clear()
    
    @staticmethod
    def _has_execution(log: 'ExecutionLogger', key: str, input: Optional[List[List[str]]]) -> bool:
        """Check if log matches the given key and input"""
        return log.key == key and ExecutionLogger._check_strategy_inputs(log.input, input)
    
    @staticmethod
    def _check_strategy_inputs(logger_inputs: Optional[List[List[str]]], inputs: Optional[List[List[str]]]) -> bool:
        """Check if strategy inputs match between logger and current inputs"""
        if not logger_inputs:
            return not inputs or len(inputs) == 0
        
        if not inputs:
            return False
        
        for strategy_input in logger_inputs:
            if len(strategy_input) >= 2:
                strategy, input_value = strategy_input[0], strategy_input[1]
                # Find matching strategy and input in current inputs
                found = any(
                    len(current_input) >= 2 and 
                    current_input[0] == strategy and 
                    current_input[1] == input_value
                    for current_input in inputs
                )
                if not found:
                    return False
        
        return True
