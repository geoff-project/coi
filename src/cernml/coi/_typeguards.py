# SPDX-FileCopyrightText: 2020-2024 CERN
# SPDX-FileCopyrightText: 2023-2024 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

"""Provice ABCs that correspond to each protocol of this package."""

import typing as t

from ._func_opt import FunctionOptimizable
from ._problem import Problem
from ._single_opt import ParamType, SingleOptimizable

if t.TYPE_CHECKING:
    from typing_extensions import TypeGuard

__all__ = (
    "AnyOptimizable",
    "is_function_optimizable",
    "is_function_optimizable_class",
    "is_optimizable",
    "is_optimizable_class",
    "is_problem",
    "is_problem_class",
    "is_single_optimizable",
    "is_single_optimizable_class",
)


def is_problem(obj: object, /) -> "TypeGuard[Problem]":
    unwrapped = getattr(obj, "unwrapped", None)
    return isinstance(unwrapped, Problem)


def is_problem_class(obj: type, /) -> "TypeGuard[type[Problem]]":
    return issubclass(obj, Problem)  # type: ignore[misc]


def is_single_optimizable(obj: object, /) -> "TypeGuard[SingleOptimizable[t.Any]]":
    unwrapped = getattr(obj, "unwrapped", None)
    return isinstance(unwrapped, SingleOptimizable)


def is_single_optimizable_class(
    obj: type, /
) -> "TypeGuard[type[SingleOptimizable[t.Any]]]":
    return issubclass(obj, SingleOptimizable)  # type: ignore[misc]


def is_function_optimizable(obj: object, /) -> "TypeGuard[FunctionOptimizable]":
    unwrapped = getattr(obj, "unwrapped", None)
    return isinstance(unwrapped, FunctionOptimizable)


def is_function_optimizable_class(
    obj: type, /
) -> "TypeGuard[type[FunctionOptimizable]]":
    return issubclass(obj, FunctionOptimizable)  # type: ignore[misc]


AnyOptimizable = SingleOptimizable[ParamType] | FunctionOptimizable[ParamType]


def is_optimizable(obj: object, /) -> "TypeGuard[FunctionOptimizable]":
    unwrapped = getattr(obj, "unwrapped", None)
    return isinstance(unwrapped, (SingleOptimizable, FunctionOptimizable))


def is_optimizable_class(obj: type, /) -> "TypeGuard[type[AnyOptimizable]]":
    return issubclass(obj, (SingleOptimizable, FunctionOptimizable))  # type: ignore[misc]
