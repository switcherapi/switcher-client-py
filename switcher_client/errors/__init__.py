class RemoteError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

class RemoteAuthError(RemoteError):
    def __init__(self, message):
        super().__init__(message)

class RemoteCriteriaError(RemoteError):
    def __init__(self, message):
        super().__init__(message)