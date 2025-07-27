class ResultDetail:
    def __init__(self, result: bool, reason: str, metadata: dict):
        self.result = result
        self.reason = reason
        self.metadata = metadata