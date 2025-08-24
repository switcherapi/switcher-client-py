from switcher_client.lib.types import Snapshot

class GlobalSnapshot:
    
    @staticmethod
    def init(snapshot: Snapshot | None):
        GlobalSnapshot.snapshotStore = snapshot

    @staticmethod
    def clear():
        GlobalSnapshot.snapshotStore = None

    @staticmethod
    def snapshot() -> Snapshot | None:
        return GlobalSnapshot.snapshotStore
    
class LoadSnapshotOptions:
    def __init__(self, fetch_remote: bool = False, watch_snapshot: bool = False):
        self.fetch_remote = fetch_remote
        self.watch_snapshot = watch_snapshot