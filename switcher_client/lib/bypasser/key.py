from switcher_client.lib.compat import Self
from switcher_client.lib.snapshot import StrategiesType
from switcher_client.lib.types import ResultDetail

class Key:
    """ Key record used to store key response when bypassing criteria execution """

    def __init__(self, key: str):
        self._key = key
        self._result = False
        self._reason = None
        self._metadata: dict = {}
        self._when: dict[str, list[str]] = {}

    def true(self) -> Self:
        """ Force a switcher value to return true """
        self._result = True
        self._reason = "Forced to True"
        return self

    def false(self) -> Self:
        """ Force a switcher value to return false """
        self._result = False
        self._reason = "Forced to False"
        return self

    def with_metadata(self, metadata: dict) -> Self:
        """ Define metadata for the response """
        self._metadata = metadata
        return self

    def when(self, strategy: str, input_strategy: str | list[str]) -> Self:
        """ Conditionally set result based on strategy """
        if any(s.value == strategy for s in StrategiesType):
            self._when[strategy] = input_strategy if isinstance(input_strategy, list) else [input_strategy]
        return self

    def get_response(self, input_list: list[str] | None) -> ResultDetail:
        """ Return key response """
        result = self._result
        if self._when and input_list is not None:
            result = self._get_result_based_on_when(input_list)

        return ResultDetail.create(result=result, reason=self._reason, metadata=self._metadata)

    @property
    def key(self):
        """ Return selected switcher name """
        return self._key

    def _get_result_based_on_when(self, input_list: list[str]) -> bool:
        """ Evaluate the when conditions to determine the result """
        for strategy_when, input_when in self._when.items():
            entry = [e for e in input_list if e[0] == strategy_when]
            if entry and entry[0][1] not in input_when:
                self._reason = f"Forced to {not self._result} when: [{', '.join(input_when)}] - input: {entry[0][1]}"
                return not self._result

        return self._result
