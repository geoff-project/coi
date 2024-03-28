# SPDX-FileCopyrightText: 2020-2024 CERN
# SPDX-FileCopyrightText: 2023-2024 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

"""Checker for the `FunctionOptimizable` ABC."""

import typing as t
from functools import partial

import numpy as np
from scipy.optimize import LinearConstraint, NonlinearConstraint

from ..protocols import Constraint, FunctionOptimizable
from ._generic import (
    assert_human_render_called,
    assert_range,
    bump_warn_arg,
    is_box,
    is_reward,
)
from ._reseed import assert_reseed


def check_function_optimizable(opt: FunctionOptimizable, warn: int = True) -> None:
    """Check the run-time invariants of the given interface."""
    assert_optimization_space(opt)
    assert_range(opt.objective_range, "objective")
    assert_constraints(opt.constraints)
    assert_matching_names(opt)
    assert_opt_return_values(opt)
    for point in _select_skeleton_points(opt):
        reseed = partial(opt.get_initial_params, point)
        assert_reseed(opt, reseed, warn=bump_warn_arg(warn))


def _select_skeleton_points(opt: FunctionOptimizable) -> list[float]:
    points = opt.override_skeleton_points()
    if points:
        return list(points)
    return [100.0, 200.0, 1000.0]


def assert_optimization_space(opt: FunctionOptimizable) -> None:
    """Check that the optimization space is a box.."""
    for point in _select_skeleton_points(opt):
        opt_space = opt.get_optimization_space(point)
        assert is_box(
            opt_space
        ), f"optimization space {opt_space} at t={point} must be a gym.spaces.Box"


def assert_constraints(constraints: t.Sequence[Constraint]) -> None:
    """Check that the list of constraints contains only constraints."""
    allowed_types = (LinearConstraint, NonlinearConstraint)
    for constraint in constraints:
        assert isinstance(constraint, allowed_types), (
            f"constraint {constraint!r} is neither LinearConstraint nor "
            f"NonlinearConstraint"
        )


def assert_matching_names(opt: FunctionOptimizable) -> None:
    """Check that all names are strings and have the correct number.

    Example:

        >>> from gymnasium.spaces import Box
        >>> class GoodEnv:
        ...     def override_skeleton_points(self):
        ...         return None
        ...     def get_objective_function_name(self):
        ...         return "BCT"
        ...     def get_param_function_names(self):
        ...         return ["Bump H", "Bump V"]
        ...     def get_optimization_space(self, time):
        ...         return Box(-1, 1, [2])
        >>> assert_matching_names(GoodEnv())
    """
    if name := opt.get_objective_function_name():
        assert isinstance(name, str), f"objective name {name!r} must be a string"
    if names := opt.get_param_function_names():
        assert not isinstance(
            names, str
        ), f"param names {names} must not be a single string"
        for point in _select_skeleton_points(opt):
            opt_space = opt.get_optimization_space(point)
            shape: t.Optional[tuple[int, ...]] = getattr(opt_space, "shape", None)
            assert (
                shape is not None
            ), f"param names require optimization space with a shape: {opt_space!r}"
            expected = int(np.prod(shape))
            assert (
                len(names) == expected
            ), f"expected {expected} parameter names, got {len(names)}"
        for param_name in names:
            assert isinstance(
                param_name, str
            ), f"parameter name {param_name} must be a string"


def assert_opt_return_values(opt: FunctionOptimizable) -> None:
    """Check the return types of `SingleOptimizable` methods."""
    for point in _select_skeleton_points(opt):
        opt_space = opt.get_optimization_space(point)
        params = opt.get_initial_params(point)
        assert params in opt_space, "parameters outside of space"
        assert isinstance(params, np.ndarray), "parameters must be NumPy array"
        params = opt_space.sample()
        low, high = opt.objective_range
        with assert_human_render_called(opt):
            loss = opt.compute_function_objective(point, params)
        assert is_reward(loss), "loss must be a float or integer"
        assert is_reward(low), "loss range must be float: {low!r}"
        assert is_reward(high), "loss range must be float: {high!r}"
        assert (
            float(low) <= float(loss) <= float(high)
        ), f"loss is out of range [{low}, {high}]: {loss!r}"
