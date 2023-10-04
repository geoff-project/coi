# SPDX-FileCopyrightText: 2020-2024 CERN
# SPDX-FileCopyrightText: 2023-2024 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

"""Test that `Problem` does not require direct inheritance."""

import typing as t

import pytest

from cernml import coi


def test_problem_is_abstract() -> None:
    class NonInheritingProblem:
        metadata: t.Dict[str, t.Any] = {"render.modes": []}
        render_mode = None
        spec = None

        def close(self) -> None:
            pass

        def render(self, mode: str = "human") -> t.Any:
            raise NotImplementedError

        @property
        def unwrapped(self) -> "NonInheritingProblem":
            return self

        def get_wrapper_attr(self, name: str) -> t.Any:
            return getattr(self, name)

    assert issubclass(NonInheritingProblem, coi.Problem)  # type: ignore[misc]


def test_render_raises() -> None:
    class Subclass(coi.Problem):
        pass

    env = Subclass()
    with pytest.raises(NotImplementedError):
        env.render()


def test_problem_requires_close() -> None:
    class NullProblemo:
        metadata: t.ClassVar[t.Dict[str, t.Any]] = {"render.modes": []}

        def render(self, mode: str = "human") -> t.Any:
            raise NotImplementedError

        def unwrapped(self) -> "NullProblemo":
            return self

    assert not issubclass(NullProblemo, coi.Problem)  # type: ignore[misc]
