from dataclasses import dataclass

from switcher_client.lib.types import Snapshot

@dataclass
class GlobalSnapshot:
    """
    GlobalSnapshot manages the global snapshot state,
    allowing it to be set, cleared, and retrieved across the application.
    """

    @staticmethod
    def init(snapshot: Snapshot | None):
        GlobalSnapshot.snapshotStore = snapshot

    @staticmethod
    def clear():
        GlobalSnapshot.snapshotStore = None

    @staticmethod
    def snapshot() -> Snapshot | None:
        return GlobalSnapshot.snapshotStore

@dataclass
class LoadSnapshotOptions:
    """
    LoadSnapshotOptions holds the options for loading a snapshot,
    including whether to fetch it remotely and whether to watch for changes.
    """

    def __init__(self, fetch_remote: bool = False, watch_snapshot: bool = False):
        self.fetch_remote = fetch_remote
        self.watch_snapshot = watch_snapshot
