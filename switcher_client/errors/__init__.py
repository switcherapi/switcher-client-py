class RemoteError(Exception):
    """ Base class for remote errors """
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

class RemoteAuthError(RemoteError):
    """ Raised when there is an authentication error with the remote service """

class RemoteCriteriaError(RemoteError):
    """ Raised when there is a criteria error with the remote service """

class RemoteSwitcherError(RemoteError):
    """ Raised when there is a switcher error with the remote service """
    def __init__(self, not_found: list):
        super().__init__(f'{', '.join(not_found)} not found')

class LocalSwitcherError(Exception):
    """ Raised when there is a switcher error with the local service """
    def __init__(self, not_found: list):
        self.message = f'{', '.join(not_found)} not found'
        super().__init__(self.message)

class LocalCriteriaError(Exception):
    """ Raised when there is a criteria error with the local service """
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

class SnapshotNotFoundError(Exception):
    """ Raised when a snapshot is not found """
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
    'SnapshotNotFoundError'
]
