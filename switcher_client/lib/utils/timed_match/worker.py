import re
import multiprocessing

from enum import Enum
from typing import List, Optional
from dataclasses import dataclass

class TaskType(Enum):
    """Types of tasks that can be sent to the worker process."""
    MATCH = "match"
    SHUTDOWN = "shutdown"

@dataclass
class WorkerTask:
    """Task sent to the worker process."""
    task_type: TaskType
    patterns: Optional[List[str]] = None
    input_value: Optional[str] = None
    use_fullmatch: Optional[bool] = None
    task_id: Optional[str] = None

@dataclass
class WorkerResult:
    """Result returned from the worker process."""
    success: bool
    result: Optional[bool] = None
    task_id: Optional[str] = None
    error: Optional[str] = None

def persistent_regex_worker(task_queue: multiprocessing.Queue, result_queue: multiprocessing.Queue):
    """
    Persistent worker function that processes regex matching tasks in a loop.
    
    This worker runs continuously, processing tasks from the task queue until
    it receives a shutdown signal or encounters an error.
    
    Args:
        task_queue: Queue to receive WorkerTask objects
        result_queue: Queue to send WorkerResult objects back to main process
    """
    try:
        while True:
            try:
                task = task_queue.get(timeout=30.0)
                
                if task.task_type == TaskType.SHUTDOWN:
                    result_queue.put(WorkerResult(success=True, task_id=task.task_id))
                    break
                elif task.task_type == TaskType.MATCH:
                    result = _process_match_task(task)
                    result_queue.put(result)
                        
            except Exception:
                # Timeout or other error getting task, continue
                continue
                
    except Exception:
        # Worker process error, exit
        try:
            result_queue.put(WorkerResult(success=False, error="Worker process error"))
        except Exception:
            pass

def _process_match_task(task: WorkerTask) -> WorkerResult:
    """
    Process a regex matching task.
    
    Args:
        task: WorkerTask containing the matching parameters
        
    Returns:
        WorkerResult with the matching result
    """
    try:
        if not task.patterns or not task.input_value:
            return WorkerResult(
                success=False,
                error="Invalid task parameters",
                task_id=task.task_id
            )
        
        match_result = False
        for pattern in task.patterns:
            if task.use_fullmatch:
                if re.fullmatch(pattern, task.input_value):
                    match_result = True
                    break
            else:
                if re.search(pattern, task.input_value):
                    match_result = True
                    break
        
        return WorkerResult(
            success=True, 
            result=match_result, 
            task_id=task.task_id
        )
    except Exception as e:
        return WorkerResult(
            success=False, 
            error=str(e), 
            task_id=task.task_id
        )