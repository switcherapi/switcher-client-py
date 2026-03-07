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

class RemoteSwitcherError(RemoteError):
    def __init__(self, not_found: list):
        super().__init__(f'{", ".join(not_found)} not found')

class LocalCriteriaError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

__all__ = [
    'RemoteError',
    'RemoteAuthError',
    'RemoteCriteriaError',
    'RemoteSwitcherError',
    'LocalCriteriaError',
]