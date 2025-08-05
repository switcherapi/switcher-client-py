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
        self.group: Optional[List[Group]] = None

class Group:
    def __init__(self):
        self.name: Optional[str] = None
        self.activated: Optional[bool] = None
        self.config: Optional[List[Config]] = None

class Config:
    def __init__(self):
        self.key: Optional[str] = None
        self.activated: Optional[bool] = None
        self.strategies: Optional[List[StrategyConfig]] = None
        self.relay: Optional[Relay] = None

class StrategyConfig:
    def __init__(self):
        self.strategy: Optional[str] = None
        self.activated: Optional[bool] = None
        self.operation: Optional[str] = None
        self.values: Optional[List[str]] = None

class Relay:
    def __init__(self):
        self.type: Optional[str] = None
        self.activated: Optional[bool] = None