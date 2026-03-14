import threading
import time

from typing import Callable, Optional

class SnapshotAutoUpdater:
    """ Schedules periodic snapshot updates in a background thread """

    def __init__(self):
        self._timer_thread: Optional[threading.Thread] = None
        self._stop_event: Optional[threading.Event] = None

    def schedule(
            self, interval: int,
            check_snapshot: Callable[[], bool],
            callback: Callable[[Optional[Exception], bool], None]) -> None:
        """
        Schedule periodic snapshot updates in a background thread.

        :param interval: Update interval in seconds
        :param check_snapshot: Function that checks and updates snapshot, returns True if updated
        :param callback: Callback function called with (error, updated) after each check
        """

        self.terminate()
        self._stop_event = threading.Event()

        self._timer_thread = threading.Thread(
            target=self._update_worker,
            args=(interval, check_snapshot, callback),
            daemon=True,
            name="SnapshotAutoUpdater"
        )
        self._timer_thread.start()

    def terminate(self) -> None:
        """
        Terminate the scheduled snapshot auto-update thread gracefully.
        """
        if self._stop_event is not None:
            self._stop_event.set()

        if self._timer_thread is not None and self._timer_thread.is_alive():
            self._timer_thread.join(timeout=5.0)

        self._timer_thread = None
        self._stop_event = None

    def _update_worker(
            self, interval: int,
            check_snapshot: Callable[[], bool],
            callback: Callable[[Optional[Exception], bool], None]) -> None:
        stop_event = self._stop_event

        time.sleep(interval) # delay start
        while stop_event is not None and not stop_event.is_set():
            try:
                updated = check_snapshot()
                callback(None, updated)
            except Exception as error:  # pylint: disable=broad-exception-caught
                callback(error, False)

            stop_event.wait(interval)
