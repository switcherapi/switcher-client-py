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