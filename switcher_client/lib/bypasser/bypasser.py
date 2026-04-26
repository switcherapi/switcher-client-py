from switcher_client.lib.bypasser.key import Key

class Bypasser:
    """
    Bypasser allows to force a switcher value to return a given value by calling one of both methods - true() false()
    """

    _bypassed_keys = []

    @staticmethod
    def assume(key: str) -> Key:
        # Remove previous forced value if exists to avoid conflicts
        Bypasser.forget(key)

        new_key = Key(key)
        Bypasser._bypassed_keys.append(new_key)
        return new_key

    @staticmethod
    def forget(key: str) -> None:
        """ Remove forced value from a switcher """
        key_stored = Bypasser.search_key(key)
        if key_stored is not None:
            Bypasser._bypassed_keys.remove(key_stored)

    @staticmethod
    def search_key(key: str) -> Key | None:
        """ Search for key registered via 'assume' """
        for bypassed_key in Bypasser._bypassed_keys:
            if bypassed_key.key == key:
                return bypassed_key

        return None
