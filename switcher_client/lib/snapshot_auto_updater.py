import threading
import time
from typing import Callable, Optional

class SnapshotAutoUpdater:
    _timer_thread: Optional[threading.Thread] = None
    _stop_event: Optional[threading.Event] = None

    @staticmethod
    def schedule(interval: int, check_snapshot: Callable[[], bool], callback: Callable[[Optional[Exception], bool], None]) -> None:
        """
        Schedule periodic snapshot updates in a background thread.
        
        :param interval: Update interval in seconds
        :param check_snapshot: Function that checks and updates snapshot, returns True if updated
        :param callback: Callback function called with (error, updated) after each check
        """

        SnapshotAutoUpdater.terminate()
        SnapshotAutoUpdater._stop_event = threading.Event() 
        
        SnapshotAutoUpdater._timer_thread = threading.Thread(
            target=SnapshotAutoUpdater._update_worker,
            args=(interval, check_snapshot, callback),
            daemon=True,
            name="SnapshotAutoUpdater"
        )
        SnapshotAutoUpdater._timer_thread.start()

    @staticmethod
    def terminate() -> None:
        """
        Terminate the scheduled snapshot auto-update thread gracefully.
        """
        if SnapshotAutoUpdater._stop_event is not None:
            SnapshotAutoUpdater._stop_event.set()
        
        if SnapshotAutoUpdater._timer_thread is not None and SnapshotAutoUpdater._timer_thread.is_alive():
            SnapshotAutoUpdater._timer_thread.join(timeout=5.0)
        
        SnapshotAutoUpdater._timer_thread = None
        SnapshotAutoUpdater._stop_event = None

    @staticmethod
    def _update_worker(interval: int, check_snapshot: Callable[[], bool], callback: Callable[[Optional[Exception], bool], None]) -> None:
        stop_event = SnapshotAutoUpdater._stop_event

        time.sleep(interval) # delay start
        while stop_event is not None and not stop_event.is_set():
            try:
                updated = check_snapshot()
                callback(None, updated)
            except Exception as error:
                callback(error, False)
            
            stop_event.wait(interval)