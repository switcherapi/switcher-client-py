class RemoteError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

class RemoteAuthError(RemoteError):
    pass

class RemoteCriteriaError(RemoteError):
    pass

class RemoteSwitcherError(RemoteError):
    def __init__(self, not_found: list):
        super().__init__(f'{', '.join(not_found)} not found')

class LocalSwitcherError(Exception):
    def __init__(self, not_found: list):
        self.message = f'{', '.join(not_found)} not found'
        super().__init__(self.message)

class LocalCriteriaError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

class SnapshpotNotFoundError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

__all__ = [
    'RemoteError',
    'RemoteAuthError',
    'RemoteCriteriaError',
    'RemoteSwitcherError',
    'LocalSwitcherError',
    'LocalCriteriaError',
    'SnapshpotNotFoundError'
]
