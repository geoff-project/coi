# SPDX-FileCopyrightText: 2020-2023 CERN
# SPDX-FileCopyrightText: 2023 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

"""Checker for the `SingleOptimizable` ABC."""

import typing as t

import gym
import numpy as np
from scipy.optimize import LinearConstraint, NonlinearConstraint

from .._single_opt import Constraint, SingleOptimizable
from ._generic import assert_range, is_box, is_reward


def check_single_optimizable(opt: SingleOptimizable, warn: bool = True) -> None:
    """Check the run-time invariants of the given interface."""
    _ = warn  # Flag is currently unused, keep it for forward compatibility.
    assert_optimization_space(opt)
    assert_range(opt.objective_range, "objective")
    assert_constraints(opt.constraints)
    assert_matching_names(opt)
    assert_opt_returned_values(opt)


def assert_optimization_space(env: SingleOptimizable) -> None:
    """Check that the spaces are boxes of the same shape.

    Example:

        >>> class Foo:
        ...     optimization_space = gym.spaces.Box(-1, 1, ())
        >>> assert_optimization_space(Foo())
    """
    opt_space = env.optimization_space
    assert is_box(opt_space), f"optimization space {opt_space} must be a gym.spaces.Box"
    if isinstance(env, gym.Env):
        act_space = env.action_space
        assert is_box(act_space), f"action space {act_space} must be a gym.spaces.Box"
        assert act_space.shape == opt_space.shape, (
            f"action {act_space.shape} and optimization {opt_space.shape} space "
            "have the same shape"
        )


def assert_constraints(constraints: t.List[Constraint]) -> None:
    """Check that the list of constraints contains only constraints."""
    allowed_types = (LinearConstraint, NonlinearConstraint)
    for constraint in constraints:
        assert isinstance(constraint, allowed_types), (
            f"constraint {constraint!r} is neither LinearConstraint nor "
            f"NonlinearConstraint"
        )


def assert_matching_names(opt: SingleOptimizable) -> None:
    """Check that all names are strings and have the correct number.

    Example:

        >>> class GoodEnv:
        ...     objective_name = "BCT"
        ...     param_names = ["Bump H", "Bump V"]
        ...     constraint_names = ["Minimum intensity"]
        ...     constraints = [object()]
        ...     optimization_space = gym.spaces.Box(-1, 1, [2])
        >>> assert_matching_names(GoodEnv())
    """
    if opt.objective_name:
        assert isinstance(
            opt.objective_name, str
        ), f"objective name {opt.objective_name} must be a string"
    if opt.param_names:
        assert not isinstance(
            opt.param_names, str
        ), f"param names {opt.param_names} must not be a single string"
        expected = np.prod(opt.optimization_space.shape)
        assert (
            len(opt.param_names) == expected
        ), f"expected {expected} parameter names, got {len(opt.param_names)}"
        for param_name in opt.param_names:
            assert isinstance(
                param_name, str
            ), f"objective name {param_name} must be a string"
    if opt.constraint_names:
        assert not isinstance(
            opt.constraint_names, str
        ), f"param names {opt.constraint_names} must not be a single string"
        expected = len(opt.constraints)
        assert (
            len(opt.constraint_names) == expected
        ), f"expected {expected} parameter names, got {len(opt.constraint_names)}"
        for constraint_name in opt.constraint_names:
            assert isinstance(
                constraint_name, str
            ), f"objective name {constraint_name} must be a string"


def assert_opt_returned_values(opt: SingleOptimizable) -> None:
    """Check the return types of `SingleOptimizable` methods."""
    params = opt.get_initial_params()
    assert params in opt.optimization_space, "parameters outside of space"
    assert isinstance(params, np.ndarray), "parameters must be NumPy array"
    loss = opt.compute_single_objective(opt.optimization_space.sample())
    assert is_reward(loss), "loss must be a float or integer"
    low, high = opt.objective_range
    assert low <= loss <= high, f"loss is out of range [{low}, {high}]: {loss}"
