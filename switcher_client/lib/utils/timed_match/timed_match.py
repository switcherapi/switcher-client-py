import multiprocessing
import time

from typing import List, Optional, Any
from dataclasses import dataclass

from ...globals.global_context import DEFAULT_REGEX_MAX_BLACKLISTED, DEFAULT_REGEX_MAX_TIME_LIMIT
from .worker import TaskType, WorkerResult, WorkerTask, persistent_regex_worker

@dataclass
class Blacklist:
    """Represents a blacklisted regex pattern and input combination."""
    patterns: List[str]
    input_value: str

class TimedMatch:
    """
    This class provides regex match operations with timeout-based ReDoS protection.
    
    Operations are executed in isolated processes with configurable timeouts.
    Processes that exceed the timeout are terminated, preventing ReDoS attacks.
    Failed operations are cached in a blacklist to avoid repeated resource usage.
    """
    
    _blacklisted: List[Blacklist] = []
    _max_blacklisted: int = DEFAULT_REGEX_MAX_BLACKLISTED
    _max_time_limit: float = DEFAULT_REGEX_MAX_TIME_LIMIT / 1000.0  # Convert to seconds
    
    # Persistent worker management
    _worker_process: Optional[multiprocessing.Process] = None
    _task_queue: Optional[multiprocessing.Queue] = None
    _result_queue: Optional[multiprocessing.Queue] = None
    _worker_ctx: Optional[Any] = None
    _task_counter: int = 0
    _worker_needs_restart: bool = False
    _old_workers_to_cleanup: List[multiprocessing.Process] = []
    
    @classmethod
    def initialize_worker(cls) -> bool:
        """
        Initialize the persistent worker process for regex matching.
        
        Creates a new worker process with communication queues. If a worker
        already exists, it will be terminated before creating a new one.
        
        Returns:
            True if worker was successfully initialized, False otherwise
        """
        # Terminate existing worker if any
        cls.terminate_worker()
        
        # Create multiprocessing context
        cls._worker_ctx = multiprocessing.get_context('spawn')
        
        # Create communication queues
        cls._task_queue = cls._worker_ctx.Queue()
        cls._result_queue = cls._worker_ctx.Queue()
        
        # Create and start worker process
        cls._worker_process = cls._worker_ctx.Process(
            target=persistent_regex_worker,
            args=(cls._task_queue, cls._result_queue)
        )
        if cls._worker_process:
            cls._worker_process.start()
        
        # Reset task counter
        cls._task_counter = 0
        
        return cls._worker_process is not None and cls._worker_process.is_alive()
    
    @classmethod
    def terminate_worker(cls) -> None:
        """
        Terminate all worker processes (current and old ones).
        
        Sends a shutdown signal to workers and forcefully terminates them if needed.
        Cleans up all worker-related resources.
        """
        try:
            # Terminate current worker
            if cls._worker_process and cls._worker_process.is_alive():
                cls._graceful_shutdown()
            
            # Terminate all old workers waiting for cleanup
            cls._terminate_all_old_workers()
        finally:
            cls._cleanup_resources()
    
    @classmethod
    def _graceful_shutdown(cls) -> None:
        """Attempt graceful shutdown of worker process."""
        if cls._task_queue:
            shutdown_task = WorkerTask(
                task_type=TaskType.SHUTDOWN,
                task_id=f"shutdown_{time.time()}"
            )
            cls._task_queue.put(shutdown_task, timeout=1.0)
            if cls._worker_process:
                cls._worker_process.join(timeout=2.0)
    
    @classmethod
    def _cleanup_resources(cls) -> None:
        """Clean up all worker-related resources."""
        cls._worker_process = None
        cls._task_queue = None
        cls._result_queue = None
        cls._worker_ctx = None
        cls._task_counter = 0
        cls._worker_needs_restart = False
        cls._old_workers_to_cleanup.clear()
    
    @classmethod
    def try_match(cls, patterns: List[str], input_value: str, use_fullmatch: bool = False) -> bool:
        """
        Executes regex matching operation with timeout protection.
        
        The operation runs in an isolated process with timeout protection to prevent
        runaway regex operations that could lead to ReDoS attacks.
        
        Failed operations (timeouts, errors) are automatically added to a blacklist
        to prevent repeated attempts with the same problematic patterns.
        
        Args:
            patterns: Array of regular expression patterns to test against the input
            input_value: The input string to match against the regex patterns
            use_fullmatch: If True, uses re.fullmatch; if False, uses re.search
            
        Returns:
            True if any of the regex patterns match the input, false otherwise
        """
        if cls._is_blacklisted(patterns, input_value):
            return False
            
        return cls._safe_match(patterns, input_value, use_fullmatch)
    
    @classmethod
    def _safe_match(cls, patterns: List[str], input_value: str, use_fullmatch: bool) -> bool:
        """ Run regex match with timeout protection using persistent worker."""
        task_id = cls._create_and_send_task(patterns, input_value, use_fullmatch)
        return cls._wait_for_result(task_id, patterns, input_value)
    
    @classmethod
    def _create_and_send_task(cls, patterns: List[str], input_value: str, use_fullmatch: bool) -> str:
        """Create task and send to worker."""
        cls._task_counter += 1
        task_id = f"task_{cls._task_counter}_{time.time()}"
        
        task = WorkerTask(
            task_type=TaskType.MATCH,
            patterns=patterns,
            input_value=input_value,
            use_fullmatch=use_fullmatch,
            task_id=task_id
        )
        
        if cls._task_queue:
            cls._task_queue.put(task, timeout=1.0)
        return task_id
    
    @classmethod
    def _wait_for_result(cls, task_id: str, patterns: List[str], input_value: str) -> bool:
        """Wait for result from worker with timeout."""
        start_time = time.time()
        while time.time() - start_time < cls._max_time_limit:
            try:
                if cls._result_queue:
                    result = cls._result_queue.get(timeout=0.1)
                    if result.task_id == task_id:
                        return cls._process_worker_result(result, patterns, input_value)
            except Exception:
                continue
        
        # Timeout occurred - start new worker immediately and defer cleanup of old one
        cls._replace_worker_immediately()
        cls._add_to_blacklist(patterns, input_value)
        return False
    
    @classmethod
    def _process_worker_result(cls, result: WorkerResult, patterns: List[str], input_value: str) -> bool:
        """Process result from worker."""
        if result.success:
            return result.result if result.result is not None else False
        else:
            cls._add_to_blacklist(patterns, input_value)
            return False
    
    @classmethod
    def _is_blacklisted(cls, patterns: List[str], input_value: str) -> bool:
        for blacklisted in cls._blacklisted:
            # Check if input can contain same segment that could fail matching
            if (blacklisted.input_value in input_value or input_value in blacklisted.input_value):
                # Check if any of the patterns match (regex order should not affect)
                matching_patterns = [p for p in patterns if p in blacklisted.patterns]
                if matching_patterns:
                    return True
        return False
    
    @classmethod
    def _add_to_blacklist(cls, patterns: List[str], input_value: str) -> None:
        # Maintain blacklist size limit
        if len(cls._blacklisted) >= cls._max_blacklisted:
            cls._blacklisted.pop(0)  # Remove oldest entry
        
        cls._blacklisted.append(Blacklist(
            patterns=patterns.copy(),
            input_value=input_value
        ))
    
    @classmethod
    def _replace_worker_immediately(cls) -> None:
        """Replace worker immediately without waiting for cleanup."""
        # Move current worker to cleanup list if it exists
        if cls._worker_process:
            cls._old_workers_to_cleanup.append(cls._worker_process)
        
        # Clear current worker references (but don't cleanup yet)
        cls._worker_process = None
        cls._task_queue = None
        cls._result_queue = None
        cls._worker_ctx = None
        cls._task_counter = 0
        
        # Initialize new worker immediately
        cls.initialize_worker()
    
    @classmethod
    def _terminate_all_old_workers(cls) -> None:
        """Forcefully terminate all old workers synchronously."""
        for worker in cls._old_workers_to_cleanup[:]:
            if worker and worker.is_alive():
                worker.terminate()
                worker.join(timeout=1.0)
        
        cls._old_workers_to_cleanup.clear()
    
    @classmethod
    def clear_blacklist(cls) -> None:
        cls._blacklisted.clear()
    
    @classmethod
    def set_max_blacklisted(cls, value: int) -> None:
        cls._max_blacklisted = value
    
    @classmethod
    def set_max_time_limit(cls, value: int) -> None:
        cls._max_time_limit = value / 1000.0  # Convert to seconds