from contextvars import ContextVar

from switcher_client.lib.bypasser.key import Key

class Bypasser:
    """
    Bypasser allows to force a switcher value to return a given value by calling one of both methods - true() false()
    """

    _bypassed_keys: ContextVar[dict[str, Key] | None] = ContextVar('bypassed_keys', default=None)

    @staticmethod
    def assume(key: str) -> Key:
        # Remove previous forced value if exists to avoid conflicts
        new_key = Key(key)
        bypassed_keys = dict(Bypasser._current_keys())
        bypassed_keys[key] = new_key
        Bypasser._bypassed_keys.set(bypassed_keys)
        return new_key

    @staticmethod
    def forget(key: str) -> None:
        """ Remove forced value from a switcher """
        bypassed_keys = dict(Bypasser._current_keys())
        if key in bypassed_keys:
            del bypassed_keys[key]
            Bypasser._bypassed_keys.set(bypassed_keys)

    @staticmethod
    def search_key(key: str) -> Key | None:
        """ Search for key registered via 'assume' """
        return Bypasser._current_keys().get(key)

    @staticmethod
    def clear() -> None:
        """ Remove all forced values from the current execution context """
        Bypasser._bypassed_keys.set({})

    @staticmethod
    def _current_keys() -> dict[str, Key]:
        bypassed_keys = Bypasser._bypassed_keys.get()
        return bypassed_keys if bypassed_keys is not None else {}
