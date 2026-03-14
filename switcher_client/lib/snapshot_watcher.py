import os
import threading

from dataclasses import dataclass, field
from typing import Callable

from .snapshot_loader import load_domain
from .globals.global_snapshot import GlobalSnapshot

_POLL_INTERVAL = 1  # seconds between file stat checks

@dataclass
class WatchSnapshotCallback:
    """ Typed callback contract for Client.watch_snapshot """
    success: Callable[[], None] = field(default_factory=lambda: (lambda: None))
    reject: Callable[[Exception], None] = field(default_factory=lambda: (lambda _: None))

class SnapshotWatcher:
    """ Watches the snapshot file for changes and updates the switcher accordingly """

    def __init__(self):
        self._stop_event: threading.Event = threading.Event()
        self._ready_event: threading.Event = threading.Event()
        self._thread: threading.Thread | None = None

    def watch_snapshot(self, snapshot_location: str, environment: str, callback: WatchSnapshotCallback) -> None:
        """ Watch snapshot file for changes and invoke callbacks on result """
        self._stop_event.clear()
        self._ready_event.clear()
        self._thread = threading.Thread(
            target=self._watch,
            args=(snapshot_location, environment, callback),
            daemon=True,
            name="SnapshotWatcher"
        )
        self._thread.start()
        self._ready_event.wait()

    def unwatch_snapshot(self) -> None:
        """ Stop watching the snapshot file """
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=5.0)
            self._thread = None

    def _watch(self, snapshot_location: str, environment: str, callback: WatchSnapshotCallback) -> None:
        snapshot_file = f"{snapshot_location}/{environment}.json"
        last_mtime = self._get_mtime(snapshot_file)
        self._ready_event.set()

        while not self._stop_event.is_set():
            self._stop_event.wait(_POLL_INTERVAL)
            current_mtime = self._get_mtime(snapshot_file)
            if current_mtime != last_mtime:
                last_mtime = current_mtime
                self._on_modify_snapshot(snapshot_location, environment, callback)

    def _get_mtime(self, snapshot_file: str) -> float:
        return os.stat(snapshot_file).st_mtime

    def _on_modify_snapshot(self, snapshot_location: str, environment: str, callback: WatchSnapshotCallback) -> None:
        try:
            snapshot = load_domain(snapshot_location, environment)
            GlobalSnapshot.init(snapshot)
            callback.success()
        except Exception as error:  # pylint: disable=broad-exception-caught
            callback.reject(error)
