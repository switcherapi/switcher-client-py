from typing import Optional, List

class ResultDetail:
    def __init__(self, result: bool, reason: str, metadata: dict):
        self.result = result
        self.reason = reason
        self.metadata = metadata

class Snapshot:
    def __init__(self):
        self.data: SnapshotData

class SnapshotData:
    def __init__(self):
        self.domain: Domain

class Domain:
    def __init__(self):
        self.name: Optional[str] = None
        self.version: int = 0
        self.activated: Optional[bool] = None


