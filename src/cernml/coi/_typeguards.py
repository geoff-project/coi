# SPDX-FileCopyrightText: 2020 - 2024 CERN
# SPDX-FileCopyrightText: 2023 - 2024 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

"""These functions let you test which interfaces an object implements.

Unlike naive :func:`isinstance()` checks, these functions takes
Gymnasium :doc:`gym:api/wrappers` into account and unwrap them. For
convenience when using Mypy, all functions return a `~typing.TypeGuard`.

The functions with name :samp:`is_{type}_class()` are relatively simple
wrappers around :func:`issubclass()`. They work around some weaknesses
in Mypy's error reporting, and provide symmetry with the
:samp:`is_{type}()` functions based on :func:`isinstance()`.

.. currentmodule:: cernml.coi
"""

import typing as t

from gymnasium import Env

from ._custom_optimizer_provider import CustomOptimizerProvider
from ._goalenv import GoalEnv
from ._sepenv import SeparableEnv, SeparableGoalEnv
from .configurable import Configurable
from .protocols import FunctionOptimizable, Problem, SingleOptimizable

if t.TYPE_CHECKING:
    from typing_extensions import TypeAlias, TypeGuard

    from .protocols import ParamType  # noqa: F401

__all__ = (
    "AnyOptimizable",
    "is_configurable",
    "is_configurable_class",
    "is_custom_optimizer_provider",
    "is_custom_optimizer_provider_class",
    "is_env",
    "is_env_class",
    "is_function_optimizable",
    "is_function_optimizable_class",
    "is_goal_env",
    "is_goal_env_class",
    "is_optimizable",
    "is_optimizable_class",
    "is_problem",
    "is_problem_class",
    "is_separable_env",
    "is_separable_env_class",
    "is_separable_goal_env",
    "is_separable_goal_env_class",
    "is_single_optimizable",
    "is_single_optimizable_class",
)


def is_configurable(obj: object, /) -> "TypeGuard[Configurable]":
    """Check whether the given object is `Configurable`."""
    unwrapped = getattr(obj, "unwrapped", None)
    return isinstance(unwrapped, Configurable)


def is_configurable_class(obj: object, /) -> "TypeGuard[type[Configurable]]":
    """Check whether the given type is a subclass of `Configurable`."""
    return isinstance(obj, type) and issubclass(obj, Configurable)


def is_problem(obj: object, /) -> "TypeGuard[Problem]":
    """Check whether the given object is a `Problem`."""
    unwrapped = getattr(obj, "unwrapped", None)
    return isinstance(unwrapped, Problem)


def is_problem_class(obj: object, /) -> "TypeGuard[type[Problem]]":
    """Check whether the given type is a subclass of `Problem`."""
    return isinstance(obj, type) and issubclass(obj, Problem)  # type: ignore[misc]


def is_single_optimizable(obj: object, /) -> "TypeGuard[SingleOptimizable[t.Any]]":
    """Check whether the given object is a `SingleOptimizable`."""
    unwrapped = getattr(obj, "unwrapped", None)
    return isinstance(unwrapped, SingleOptimizable)


def is_single_optimizable_class(
    obj: object, /
) -> "TypeGuard[type[SingleOptimizable[t.Any]]]":
    """Check whether the given type is a subclass of `SingleOptimizable`."""
    return isinstance(obj, type) and issubclass(obj, SingleOptimizable)  # type: ignore[misc]


def is_function_optimizable(obj: object, /) -> "TypeGuard[FunctionOptimizable]":
    """Check whether the given object is a `FunctionOptimizable`."""
    unwrapped = getattr(obj, "unwrapped", None)
    return isinstance(unwrapped, FunctionOptimizable)


def is_function_optimizable_class(
    obj: object, /
) -> "TypeGuard[type[FunctionOptimizable]]":
    """Check whether the given type is a subclass of `FunctionOptimizable`."""
    return isinstance(obj, type) and issubclass(obj, FunctionOptimizable)  # type: ignore[misc]


AnyOptimizable: "TypeAlias" = (
    "SingleOptimizable[ParamType] | FunctionOptimizable[ParamType]"
)


def is_optimizable(obj: object, /) -> "TypeGuard[AnyOptimizable]":
    """Combined check for `SingleOptimizable`/`FunctionOptimizable`."""
    unwrapped = getattr(obj, "unwrapped", None)
    return isinstance(unwrapped, (SingleOptimizable, FunctionOptimizable))


def is_optimizable_class(obj: object, /) -> "TypeGuard[type[AnyOptimizable]]":
    """Combined check for `SingleOptimizable`/`FunctionOptimizable`."""
    return isinstance(obj, type) and issubclass(  # type: ignore[misc]
        obj,
        (SingleOptimizable, FunctionOptimizable),
    )


def is_env(obj: object, /) -> "TypeGuard[Env]":
    """Check whether the given object is an `~gymnasium.Env`."""
    unwrapped = getattr(obj, "unwrapped", None)
    return isinstance(unwrapped, Env)


def is_env_class(obj: object, /) -> "TypeGuard[type[Env]]":
    """Check whether the given type is a subclass of `~gymnasium.Env`."""
    return isinstance(obj, type) and issubclass(obj, Env)


def is_goal_env(obj: object, /) -> "TypeGuard[GoalEnv]":
    """Check whether the given object is a `GoalEnv`."""
    unwrapped = getattr(obj, "unwrapped", None)
    return isinstance(unwrapped, GoalEnv)


def is_goal_env_class(obj: object, /) -> "TypeGuard[type[GoalEnv]]":
    """Check whether the given type is a subclass of `GoalEnv`."""
    return isinstance(obj, type) and issubclass(obj, GoalEnv)


def is_separable_env(obj: object, /) -> "TypeGuard[SeparableEnv]":
    """Check whether the given object is a `SeparableEnv`."""
    unwrapped = getattr(obj, "unwrapped", None)
    return isinstance(unwrapped, SeparableEnv)


def is_separable_env_class(obj: object, /) -> "TypeGuard[type[SeparableEnv]]":
    """Check whether the given type is a subclass of `SeparableEnv`."""
    return isinstance(obj, type) and issubclass(obj, SeparableEnv)


def is_separable_goal_env(obj: object, /) -> "TypeGuard[SeparableGoalEnv]":
    """Check whether the given object is a `SeparableGoalEnv`."""
    unwrapped = getattr(obj, "unwrapped", None)
    return isinstance(unwrapped, SeparableGoalEnv)


def is_separable_goal_env_class(obj: object, /) -> "TypeGuard[type[SeparableGoalEnv]]":
    """Check whether the given type is a subclass of `SeparableGoalEnv`."""
    return isinstance(obj, type) and issubclass(obj, SeparableGoalEnv)


def is_custom_optimizer_provider(
    obj: object, /
) -> "TypeGuard[CustomOptimizerProvider]":
    """Check whether the given object is a `CustomOptimizerProvider`."""
    # This class is special! it may not have an `unwrapped` property.
    unwrapped = getattr(obj, "unwrapped", obj)
    return isinstance(unwrapped, CustomOptimizerProvider)


def is_custom_optimizer_provider_class(
    obj: object, /
) -> "TypeGuard[type[CustomOptimizerProvider]]":
    """Check whether the type is a subclass of `CustomOptimizerProvider`."""
    return isinstance(obj, type) and issubclass(obj, CustomOptimizerProvider)
