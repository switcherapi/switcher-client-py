from switcher_client.lib.types import ResultDetail

class Key:
    """ Key record used to store key response when bypassing criteria execution """

    def __init__(self, key: str):
        self._key = key
        self._result = None

    def true(self):
        """ Force a switcher value to return true """
        self._result = True

    def get_response(self, input_list: list[str]) -> ResultDetail:
        return ResultDetail.create(result=True, reason=f"Forced to '{self._result}' - input: {input_list}")

    @property
    def key(self):
        """ Get the key of the switcher """
        return self._key
