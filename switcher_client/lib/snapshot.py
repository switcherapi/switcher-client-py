from switcher_client.lib.types import Snapshot, SnapshotData, Domain


def load_domain(snpahsot_location: str, environment: str):
    """ Load Domain from snapshot file """
    
    snapshot_file = f"{snpahsot_location}/{environment}.json"

    print(f"Loading snapshot from {snapshot_file}")
    snapshot_data = SnapshotData()
    snapshot_data.domain = Domain()
    snapshot_data.domain.version = 1
    
    snapshot = Snapshot()
    snapshot.data = snapshot_data
    return snapshot