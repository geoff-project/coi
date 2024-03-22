# SPDX-FileCopyrightText: 2020-2024 CERN
# SPDX-FileCopyrightText: 2023-2024 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

"""Test that `Problem` does not require direct inheritance."""

from __future__ import annotations

import typing as t
from unittest.mock import Mock

import pytest

from cernml import coi


def test_problem_is_abstract() -> None:
    class NonInheritingProblem:
        metadata: t.ClassVar[dict[str, t.Any]] = {"render_modes": []}
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
        metadata: t.ClassVar[dict[str, t.Any]] = {"render_modes": []}

        def render(self, mode: str = "human") -> t.Any:
            raise NotImplementedError

        def unwrapped(self) -> "NullProblemo":
            return self

    assert not coi.is_problem_class(NullProblemo)


@pytest.mark.parametrize("render_mode", ["human", None])
def test_base_problem_sets_render_mode(render_mode: str | None) -> None:
    class Subclass(coi.BaseProblem):
        metadata = {"render_modes": ["human"]}

    env = Subclass(render_mode=render_mode)
    assert env.render_mode == render_mode


def test_base_problem_context_manager() -> None:
    env = coi.BaseProblem()
    env.close = Mock(wraps=env.close)  # type: ignore[method-assign]
    with env as ctx:
        assert ctx is env
    env.close.assert_called_once_with()
