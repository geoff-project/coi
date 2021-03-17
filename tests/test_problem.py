"""Test that `Problem` does not require direct inheritance."""
# pylint: disable = missing-class-docstring, missing-function-docstring

import typing as t

from cernml import coi


def test_problem_is_abstract() -> None:
    class NonInheritingProblem:
        metadata: t.Dict[str, t.Any] = {"render.modes": []}

        def close(self) -> None:
            pass

        def render(self, mode: str = "human") -> t.Any:
            raise NotImplementedError()

        def unwrapped(self) -> "NonInheritingProblem":
            return self

    assert issubclass(NonInheritingProblem, coi.Problem)


def test_problem_requires_close() -> None:
    class NullProblemo:
        metadata: t.Dict[str, t.Any] = {"render.modes": []}

        def render(self, mode: str = "human") -> t.Any:
            raise NotImplementedError()

        def unwrapped(self) -> "NullProblemo":
            return self

    assert not issubclass(NullProblemo, coi.Problem)
