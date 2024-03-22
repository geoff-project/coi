# SPDX-FileCopyrightText: 2020-2024 CERN
# SPDX-FileCopyrightText: 2023-2024 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

"""Test the `_typeguards` module."""

import typing as t
from unittest.mock import Mock

import gymnasium as gym
import pytest

from cernml import coi
from cernml.coi._machinery import AttrCheckProtocol

TYPE_MAP: tuple[
    tuple[
        type[AttrCheckProtocol],
        t.Callable[[object], bool],
        t.Callable[[object], bool],
    ],
    ...,
] = (
    (coi.Configurable, coi.is_configurable, coi.is_configurable_class),
    (gym.Env, coi.is_env, coi.is_env_class),
    (
        coi.FunctionOptimizable,
        coi.is_function_optimizable,
        coi.is_function_optimizable_class,
    ),
    (coi.GoalEnv, coi.is_goal_env, coi.is_goal_env_class),
    (coi.Problem, coi.is_problem, coi.is_problem_class),
    (coi.SeparableEnv, coi.is_separable_env, coi.is_separable_env_class),
    (
        coi.SeparableGoalEnv,
        coi.is_separable_goal_env,
        coi.is_separable_goal_env_class,
    ),
    (
        coi.SingleOptimizable,
        coi.is_single_optimizable,
        coi.is_single_optimizable_class,
    ),
    (
        coi.CustomOptimizerProvider,
        coi.is_custom_optimizer_provider,
        coi.is_custom_optimizer_provider_class,
    ),
)
# coi.Optimizable: (coi.is_optimizable, coi.is_optimizable_class),


def test_complete() -> None:
    tested_names = {func.__name__ for funcs in TYPE_MAP for func in funcs[1:]} | {
        "AnyOptimizable",
        "is_optimizable",
        "is_optimizable_class",
    }
    missed_names = set(coi._typeguards.__all__) - tested_names
    assert not missed_names


def test_any_optimizable() -> None:
    class ConcreteSingleOptimizable(coi.SingleOptimizable):
        optimization_space: t.Any = None

        def get_initial_params(self) -> t.Any:
            pass

        def compute_single_objective(self, params: t.Any) -> t.Any:
            pass

    class ConcreteFunctionOptimizable(coi.FunctionOptimizable):
        def get_optimization_space(self, cycle_time: float) -> t.Any:
            pass

        def get_initial_params(self, cycle_time: float) -> t.Any:
            pass

        def compute_function_objective(self, cycle_time: float, params: t.Any) -> t.Any:
            pass

    assert coi.is_optimizable(ConcreteSingleOptimizable())
    assert coi.is_optimizable(ConcreteFunctionOptimizable())
    assert coi.is_optimizable_class(ConcreteSingleOptimizable)
    assert coi.is_optimizable_class(ConcreteFunctionOptimizable)
    assert not coi.is_optimizable(1)
    assert not coi.is_optimizable_class(int)


@pytest.mark.parametrize(("cls", "is_instance", "is_subclass"), TYPE_MAP)
def test_typeguard(
    cls: type[AttrCheckProtocol],
    is_instance: t.Callable[[object], bool],
    is_subclass: t.Callable[[object], bool],
) -> None:
    attr_list = getattr(cls, "__protocol_attrs__", ())
    bases = (coi.SeparableGoalEnv, coi.GoalEnv, coi.SeparableEnv, gym.Env)
    for base in bases:
        if base in cls.__mro__:
            break
    else:
        base = object

    class Subclass(base):  # type: ignore[misc, valid-type]
        for name in attr_list:
            locals()[name] = (
                classmethod(Mock(name=name))
                if isinstance(vars(cls).get(name), classmethod)
                else Mock(name=name)
            )

        @property
        def unwrapped(self) -> "Subclass":
            return self

    instance = Subclass()
    assert is_instance(instance)
    assert is_subclass(Subclass)
