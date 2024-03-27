# SPDX-FileCopyrightText: 2020-2024 CERN
# SPDX-FileCopyrightText: 2023-2024 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

"""Provice ABCs that correspond to each protocol of this package."""

import typing as t

from gymnasium import Env

from ._configurable import Configurable
from ._custom_optimizer_provider import CustomOptimizerProvider
from ._extra_envs import SeparableEnv
from ._extra_goal_envs import SeparableGoalEnv
from ._goalenv import GoalEnv
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
    """Check whether the given `Problem` is `Configurable`.

    Unlike naive `isinstance()` checks, this takes gymnasium wrappers
    into account and unwraps them. For convenience when using Mypy, this
    is a `~typing.TypeGuard`.
    """
    unwrapped = getattr(obj, "unwrapped", None)
    return isinstance(unwrapped, Configurable)


def is_configurable_class(obj: object, /) -> "TypeGuard[type[Configurable]]":
    """Check whether the given type is a subclass of `Configurable`.

    This is a simple wrapper around `issubclass()`. Its purpose is to
    work around some weaknesses in Mypy's reporting, and symmetry with
    the ``is_*()`` functions based on `isinstance()`.
    """
    return isinstance(obj, type) and issubclass(obj, Configurable)


def is_problem(obj: object, /) -> "TypeGuard[Problem]":
    """Check whether the given object is a `Problem`.

    Unlike naive `isinstance()` checks, this takes gymnasium wrappers
    into account and unwraps them. For convenience when using Mypy, this
    is a `~typing.TypeGuard`.
    """
    unwrapped = getattr(obj, "unwrapped", None)
    return isinstance(unwrapped, Problem)


def is_problem_class(obj: object, /) -> "TypeGuard[type[Problem]]":
    """Check whether the given type is a subclass of `Problem`.

    This is a simple wrapper around `issubclass()`. Its purpose is to
    work around some weaknesses in Mypy's reporting, and symmetry with
    the ``is_*()`` functions based on `isinstance()`.
    """
    return isinstance(obj, type) and issubclass(obj, Problem)  # type: ignore[misc]


def is_single_optimizable(obj: object, /) -> "TypeGuard[SingleOptimizable[t.Any]]":
    """Check whether the given `Problem` is a `SingleOptimizable`.

    Unlike naive `isinstance()` checks, this takes gymnasium wrappers
    into account and unwraps them. For convenience when using Mypy, this
    is a `~typing.TypeGuard`.
    """
    unwrapped = getattr(obj, "unwrapped", None)
    return isinstance(unwrapped, SingleOptimizable)


def is_single_optimizable_class(
    obj: object, /
) -> "TypeGuard[type[SingleOptimizable[t.Any]]]":
    """Check whether the given type is a subclass of `SingleOptimizable`.

    This is a simple wrapper around `issubclass()`. Its purpose is to
    work around some weaknesses in Mypy's reporting, and symmetry with
    the ``is_*()`` functions based on `isinstance()`.
    """
    return isinstance(obj, type) and issubclass(obj, SingleOptimizable)  # type: ignore[misc]


def is_function_optimizable(obj: object, /) -> "TypeGuard[FunctionOptimizable]":
    """Check whether the given `Problem` is a `FunctionOptimizable`.

    Unlike naive `isinstance()` checks, this takes gymnasium wrappers
    into account and unwraps them. For convenience when using Mypy, this
    is a `~typing.TypeGuard`.
    """
    unwrapped = getattr(obj, "unwrapped", None)
    return isinstance(unwrapped, FunctionOptimizable)


def is_function_optimizable_class(
    obj: object, /
) -> "TypeGuard[type[FunctionOptimizable]]":
    """Check whether the given type is a subclass of `FunctionOptimizable`.

    This is a simple wrapper around `issubclass()`. Its purpose is to
    work around some weaknesses in Mypy's reporting, and symmetry with
    the ``is_*()`` functions based on `isinstance()`.
    """
    return isinstance(obj, type) and issubclass(obj, FunctionOptimizable)  # type: ignore[misc]


AnyOptimizable: "TypeAlias" = (
    "SingleOptimizable[ParamType] | FunctionOptimizable[ParamType]"
)


def is_optimizable(obj: object, /) -> "TypeGuard[AnyOptimizable]":
    """Combined check for `SingleOptimizable`/`FunctionOptimizable`.

    Unlike naive `isinstance()` checks, this takes gymnasium wrappers
    into account and unwraps them. For convenience when using Mypy, this
    is a `~typing.TypeGuard`.
    """
    unwrapped = getattr(obj, "unwrapped", None)
    return isinstance(unwrapped, (SingleOptimizable, FunctionOptimizable))


def is_optimizable_class(obj: object, /) -> "TypeGuard[type[AnyOptimizable]]":
    """Combined check for `SingleOptimizable`/`FunctionOptimizable`.

    This is a simple wrapper around `issubclass()`. Its purpose is to
    work around some weaknesses in Mypy's reporting, and symmetry with
    the ``is_*()`` functions based on `isinstance()`.
    """
    return isinstance(obj, type) and issubclass(  # type: ignore[misc]
        obj,
        (SingleOptimizable, FunctionOptimizable),
    )


def is_env(obj: object, /) -> "TypeGuard[Env]":
    """Check whether the given `Problem` is a `~gymnasium.Env`.

    Unlike naive `isinstance()` checks, this takes gymnasium wrappers
    into account and unwraps them. For convenience when using Mypy, this
    is a `~typing.TypeGuard`.
    """
    unwrapped = getattr(obj, "unwrapped", None)
    return isinstance(unwrapped, Env)


def is_env_class(obj: object, /) -> "TypeGuard[type[Env]]":
    """Check whether the given type is a subclass of `~gymnasium.Env`.

    This is a simple wrapper around `issubclass()`. Its purpose is to
    work around some weaknesses in Mypy's reporting, and symmetry with
    the ``is_*()`` functions based on `isinstance()`.
    """
    return isinstance(obj, type) and issubclass(obj, Env)


def is_goal_env(obj: object, /) -> "TypeGuard[GoalEnv]":
    """Check whether the given `Problem` is a `GoalEnv`.

    Unlike naive `isinstance()` checks, this takes gymnasium wrappers
    into account and unwraps them. For convenience when using Mypy, this
    is a `~typing.TypeGuard`.
    """
    unwrapped = getattr(obj, "unwrapped", None)
    return isinstance(unwrapped, GoalEnv)


def is_goal_env_class(obj: object, /) -> "TypeGuard[type[GoalEnv]]":
    """Check whether the given type is a subclass of `GoalEnv`.

    This is a simple wrapper around `issubclass()`. Its purpose is to
    work around some weaknesses in Mypy's reporting, and symmetry with
    the ``is_*()`` functions based on `isinstance()`.
    """
    return isinstance(obj, type) and issubclass(obj, GoalEnv)


def is_separable_env(obj: object, /) -> "TypeGuard[SeparableEnv]":
    """Check whether the given `Problem` is a `SeparableEnv`.

    Unlike naive `isinstance()` checks, this takes gymnasium wrappers
    into account and unwraps them. For convenience when using Mypy, this
    is a `~typing.TypeGuard`.
    """
    unwrapped = getattr(obj, "unwrapped", None)
    return isinstance(unwrapped, SeparableEnv)


def is_separable_env_class(obj: object, /) -> "TypeGuard[type[SeparableEnv]]":
    """Check whether the given type is a subclass of `SeparableEnv`.

    This is a simple wrapper around `issubclass()`. Its purpose is to
    work around some weaknesses in Mypy's reporting, and symmetry with
    the ``is_*()`` functions based on `isinstance()`.
    """
    return isinstance(obj, type) and issubclass(obj, SeparableEnv)


def is_separable_goal_env(obj: object, /) -> "TypeGuard[SeparableGoalEnv]":
    """Check whether the given `Problem` is a `SeparableGoalEnv`.

    Unlike naive `isinstance()` checks, this takes gymnasium wrappers
    into account and unwraps them. For convenience when using Mypy, this
    is a `~typing.TypeGuard`.
    """
    unwrapped = getattr(obj, "unwrapped", None)
    return isinstance(unwrapped, SeparableGoalEnv)


def is_separable_goal_env_class(obj: object, /) -> "TypeGuard[type[SeparableGoalEnv]]":
    """Check whether the given type is a subclass of `SeparableGoalEnv`.

    This is a simple wrapper around `issubclass()`. Its purpose is to
    work around some weaknesses in Mypy's reporting, and symmetry with
    the ``is_*()`` functions based on `isinstance()`.
    """
    return isinstance(obj, type) and issubclass(obj, SeparableGoalEnv)


def is_custom_optimizer_provider(
    obj: object, /
) -> "TypeGuard[CustomOptimizerProvider]":
    """Check whether the given `Problem` is a `CustomOptimizerProvider`.

    Unlike naive `isinstance()` checks, this takes gymnasium wrappers
    into account and unwraps them. For convenience when using Mypy, this
    is a `~typing.TypeGuard`.
    """
    # This class is special! it may not have an `unwrapped` property.
    unwrapped = getattr(obj, "unwrapped", obj)
    return isinstance(unwrapped, CustomOptimizerProvider)


def is_custom_optimizer_provider_class(
    obj: object, /
) -> "TypeGuard[type[CustomOptimizerProvider]]":
    """Check whether the type is a subclass of `CustomOptimizerProvider`.

    This is a simple wrapper around `issubclass()`. Its purpose is to
    work around some weaknesses in Mypy's reporting, and symmetry with
    the ``is_*()`` functions based on `isinstance()`.
    """
    return isinstance(obj, type) and issubclass(obj, CustomOptimizerProvider)
