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
from gymnasium.spaces import Box

from cernml import coi


class ConcreteEnv(Env):
    pass


class ConcreteOptEnv(coi.OptEnv):
    optimization_space = Box(-1, 1)


class ConcreteGoalEnv(coi.GoalEnv):
    pass


class ConcreteOptGoalEnv(coi.OptGoalEnv):
    optimization_space = Box(-1, 1)


class ConcreteSeparableEnv(coi.SeparableEnv):
    pass


class ConcreteSeparableOptEnv(coi.SeparableOptEnv):
    optimization_space = Box(-1, 1)


class ConcreteSeparableGoalEnv(coi.SeparableGoalEnv):
    pass


class ConcreteSeparableOptGoalEnv(coi.SeparableOptGoalEnv):
    optimization_space = Box(-1, 1)


@pytest.mark.parametrize(
    ("abc", "env_class"),
    [
        (coi.OptEnv, Env),
        (coi.OptGoalEnv, coi.GoalEnv),
        (coi.SeparableOptEnv, coi.SeparableEnv),
        (coi.SeparableOptGoalEnv, coi.SeparableGoalEnv),
    ],
)
def test_is_abstract_base_class(abc: type, env_class: type[Env]) -> None:
    def body(ns: dict[str, t.Any]) -> None:
        ns["optimization_space"] = None

    mock = new_class(
        "NoDirectInheritance", bases=(coi.SingleOptimizable, env_class), exec_body=body
    )
    assert issubclass(mock, abc)


def test_env_problem() -> None:
    assert coi.is_problem_class(Env)


@pytest.mark.parametrize(
    ("subclass", "superclasses"),
    [
        (ConcreteEnv, [Env]),
        (ConcreteOptEnv, [Env, coi.SingleOptimizable, coi.OptEnv]),
        (ConcreteGoalEnv, [Env, coi.GoalEnv]),
        (
            ConcreteOptGoalEnv,
            [Env, coi.GoalEnv, coi.SingleOptimizable, coi.OptEnv, coi.OptGoalEnv],
        ),
        (
            ConcreteSeparableEnv,
            [Env, coi.SeparableEnv],
        ),
        (
            ConcreteSeparableOptEnv,
            [
                Env,
                coi.SingleOptimizable,
                coi.OptEnv,
                coi.SeparableEnv,
                coi.SeparableOptEnv,
            ],
        ),
        # SeparableGoalEnv is not a SeparableEnv. Their compute_reward()
        # methods are semantically different.
        (ConcreteSeparableGoalEnv, [Env, coi.GoalEnv, coi.SeparableGoalEnv]),
        # SeparableOptGoalEnv is not a SeparableEnv. Their compute_reward()
        # methods are semantically different.
        (
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
        ),
    ],
)
def test_env_superclasses(subclass: type, superclasses: Sequence[type]) -> None:
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


@pytest.mark.parametrize(
    "cls",
    [
        Env,
        coi.GoalEnv,
        coi.SingleOptimizable,
        coi.OptEnv,
        coi.OptGoalEnv,
        coi.SeparableEnv,
        coi.SeparableGoalEnv,
        coi.SeparableOptEnv,
        coi.SeparableOptGoalEnv,
    ],
)
def test_failures(cls: type) -> None:
    assert not issubclass(int, cls)


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
