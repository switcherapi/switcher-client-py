import inspect

from copy import deepcopy
from functools import wraps
from typing import Any, Callable

from switcher_client.client import Client
from switcher_client.lib.compat import Self

class TestAssumption:
    """Builder for a test-scoped feature flag assumption."""

    def __init__(self, key: str, operations: list[tuple[str, tuple[Any, ...]]] | None = None):
        self._key = key
        self._operations = operations or []

    def true(self) -> Self:
        self._operations.append(('true', ()))
        return self

    def false(self) -> Self:
        self._operations.append(('false', ()))
        return self

    def when(self, strategy: str, input_strategy: str | list[str]) -> Self:
        self._operations.append(('when', (strategy, input_strategy)))
        return self

    def with_metadata(self, metadata: dict) -> Self:
        self._operations.append(('with_metadata', (metadata,)))
        return self

    @property
    def key(self) -> str:
        return self._key

    def apply(self) -> None:
        assumed_key = Client.assume(self._key)

        for operation_name, args in self._operations:
            getattr(assumed_key, operation_name)(*args)

    def clone(self) -> 'TestAssumption':
        return TestAssumption(
            self._key,
            [
                (operation_name, deepcopy(args))
                for operation_name, args in self._operations
            ]
        )

def assume_test(key: str) -> TestAssumption:
    """Build a test-scoped feature flag assumption."""
    return TestAssumption(key)

def switcher_test(*assumptions: TestAssumption) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Wrap a test function with one or more temporary feature flag assumptions."""
    frozen_assumptions = _freeze_assumptions(assumptions)

    def decorator(test_function: Callable[..., Any]) -> Callable[..., Any]:
        if inspect.iscoroutinefunction(test_function):
            @wraps(test_function)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                assumption_keys = _apply_assumptions(frozen_assumptions)
                try:
                    return await test_function(*args, **kwargs)
                finally:
                    _forget_assumptions(assumption_keys)

            return async_wrapper

        @wraps(test_function)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            assumption_keys = _apply_assumptions(frozen_assumptions)
            try:
                return test_function(*args, **kwargs)
            finally:
                _forget_assumptions(assumption_keys)

        return wrapper

    return decorator

def _freeze_assumptions(assumptions: tuple[TestAssumption, ...]) -> tuple[TestAssumption, ...]:
    if not assumptions:
        raise ValueError('switcher_test requires at least one test assumption')

    for assumption in assumptions:
        if not isinstance(assumption, TestAssumption):
            raise TypeError('switcher_test expects values created with assume_test(...)')

    return tuple(assumption.clone() for assumption in assumptions)

def _apply_assumptions(assumptions: tuple[TestAssumption, ...]) -> list[str]:
    assumption_keys: list[str] = []

    try:
        for assumption in assumptions:
            assumption.apply()
            assumption_keys.append(assumption.key)
    except Exception:
        _forget_assumptions(assumption_keys)
        raise

    return assumption_keys

def _forget_assumptions(assumption_keys: list[str]) -> None:
    for key in reversed(assumption_keys):
        Client.forget(key)
