# SPDX-FileCopyrightText: 2020-2024 CERN
# SPDX-FileCopyrightText: 2023-2024 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

"""Test the inheritance chain of the package."""

import typing as t
from collections.abc import Sequence
from types import new_class

import pytest
from gymnasium import Env

from cernml import coi


class ConcreteEnv(Env):
    pass


class ConcreteOptEnv(coi.OptEnv):
    pass


class ConcreteGoalEnv(coi.GoalEnv):
    pass


class ConcreteOptGoalEnv(coi.OptGoalEnv):
    pass


class ConcreteSeparableEnv(coi.SeparableEnv):
    pass


class ConcreteSeparableOptEnv(coi.SeparableOptEnv):
    pass


class ConcreteSeparableGoalEnv(coi.SeparableGoalEnv):
    pass


class ConcreteSeparableOptGoalEnv(coi.SeparableOptGoalEnv):
    pass


def _assert_env_subclass(subclass: type, superclasses: Sequence[type]) -> None:
    all_superclasses = (
        coi.GoalEnv,
        coi.SingleOptimizable,
        coi.OptEnv,
        coi.OptGoalEnv,
        coi.SeparableEnv,
        coi.SeparableOptEnv,
        coi.SeparableGoalEnv,
        coi.SeparableOptGoalEnv,
    )
    for superclass in all_superclasses:
        assert (superclass in superclasses) == issubclass(subclass, superclass), (
            f"{subclass.__name__} < {superclass.__name__} "
            f"(bases: {', '.join([base.__name__ for base in subclass.__mro__])})"
        )


def _is_abstract_base_class(abc: type, env_class: type[Env]) -> bool:
    mock = new_class("NoDirectInheritance", bases=(coi.SingleOptimizable, env_class))
    return issubclass(mock, abc)


def test_env_problem() -> None:
    assert coi.is_problem_class(Env)


def test_optenv_is_abstract() -> None:
    assert _is_abstract_base_class(coi.OptEnv, Env)


def test_optgoalenv_is_abstract() -> None:
    assert _is_abstract_base_class(coi.OptGoalEnv, coi.GoalEnv)


def test_sepoptenv_is_abstract() -> None:
    assert _is_abstract_base_class(coi.SeparableOptEnv, coi.SeparableEnv)


def test_sepoptgoalenv_is_abstract() -> None:
    assert _is_abstract_base_class(coi.SeparableOptGoalEnv, coi.SeparableGoalEnv)


def test_env() -> None:
    _assert_env_subclass(ConcreteEnv, [Env])


def test_optenv() -> None:
    _assert_env_subclass(
        ConcreteOptEnv,
        [Env, coi.SingleOptimizable, coi.OptEnv],
    )


def test_goalenv() -> None:
    _assert_env_subclass(ConcreteGoalEnv, [Env, coi.GoalEnv])


def test_optgoalenv() -> None:
    _assert_env_subclass(
        ConcreteOptGoalEnv,
        [Env, coi.GoalEnv, coi.SingleOptimizable, coi.OptEnv, coi.OptGoalEnv],
    )


def test_sepenv() -> None:
    _assert_env_subclass(
        ConcreteSeparableEnv,
        [Env, coi.SeparableEnv],
    )


def test_sepoptenv() -> None:
    _assert_env_subclass(
        ConcreteSeparableOptEnv,
        [
            Env,
            coi.SingleOptimizable,
            coi.OptEnv,
            coi.SeparableEnv,
            coi.SeparableOptEnv,
        ],
    )


def test_sepgoalenv() -> None:
    # SeparableGoalEnv is not a SeparableEnv. Their compute_reward()
    # methods are semantically different.
    _assert_env_subclass(
        ConcreteSeparableGoalEnv,
        [Env, coi.GoalEnv, coi.SeparableGoalEnv],
    )


def test_sepoptgoalenv() -> None:
    # SeparableOptGoalEnv is not a SeparableEnv. Their compute_reward()
    # methods are semantically different.
    _assert_env_subclass(
        ConcreteSeparableOptGoalEnv,
        [
            Env,
            coi.GoalEnv,
            coi.SingleOptimizable,
            coi.OptEnv,
            coi.OptGoalEnv,
            coi.SeparableGoalEnv,
            coi.SeparableOptGoalEnv,
        ],
    )


def test_failures() -> None:
    assert not issubclass(int, Env)
    assert not issubclass(int, coi.GoalEnv)
    assert not issubclass(int, coi.SingleOptimizable)  # type: ignore[misc]
    assert not issubclass(int, coi.OptEnv)
    assert not issubclass(int, coi.OptGoalEnv)
    assert not issubclass(int, coi.SeparableEnv)
    assert not issubclass(int, coi.SeparableGoalEnv)
    assert not issubclass(int, coi.SeparableOptEnv)
    assert not issubclass(int, coi.SeparableOptGoalEnv)


@pytest.mark.parametrize(
    "cls", [coi.OptEnv, coi.OptGoalEnv, coi.SeparableOptEnv, coi.SeparableOptGoalEnv]
)
def test_subclasses_arent_magic(cls: type[coi.Problem]) -> None:
    # pylint: disable = too-few-public-methods
    class Subclass(cls):  # type: ignore[misc, valid-type]
        pass

    bases = [b for b in cls.__bases__ if b is not t.Generic]

    class ImplementsProtocol(*bases):  # type: ignore[misc]
        reset = ...
        step = ...
        get_initial_params = ...
        compute_single_objective = ...

    for base in bases:
        assert issubclass(ImplementsProtocol, base)
    assert not issubclass(ImplementsProtocol, Subclass)
