# SPDX-FileCopyrightText: 2020 - 2025 CERN
# SPDX-FileCopyrightText: 2023 - 2025 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

"""Checker for the `SingleOptimizable` ABC."""

import typing as t

import gymnasium as gym
import numpy as np
from scipy.optimize import LinearConstraint, NonlinearConstraint

from .._typeguards import is_single_optimizable
from ..protocols import Constraint, SingleOptimizable
from ._generic import assert_human_render_called, bump_warn_arg, is_box, is_reward
from ._reseed import assert_reseed


def check_single_optimizable(opt: SingleOptimizable, warn: int = True) -> None:
    """Check the run-time invariants of the given interface."""
    assert is_single_optimizable(opt), (
        f"doesn't implement the SingleOptimizable API: {opt!r}"
    )
    assert_optimization_space(opt)
    assert_constraints(opt.constraints)
    assert_matching_names(opt)
    assert_opt_return_values(opt)
    assert_reseed(opt, opt.get_initial_params, warn=bump_warn_arg(warn))


def assert_optimization_space(env: SingleOptimizable) -> None:
    """Check that the spaces are boxes of the same shape.

    Example:

        >>> class Foo:
        ...     optimization_space = gym.spaces.Box(-1, 1, ())
        ...     @property
        ...     def unwrapped(self):
        ...         return self
        >>> assert_optimization_space(Foo())
    """
    opt_space = env.optimization_space
    assert is_box(opt_space), f"optimization space {opt_space} must be a gym.spaces.Box"
    if isinstance(env.unwrapped, gym.Env):
        act_space = t.cast(gym.Env, env).action_space
        assert is_box(act_space), f"action space {act_space} must be a gym.spaces.Box"
        assert act_space.shape == opt_space.shape, (
            f"action {act_space.shape} and optimization {opt_space.shape} space "
            "have the same shape"
        )


def assert_constraints(constraints: t.Sequence[Constraint]) -> None:
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
        assert isinstance(opt.objective_name, str), (
            f"objective name {opt.objective_name!r} must be a string"
        )
    if opt.param_names:
        assert not isinstance(opt.param_names, str), (
            f"param names {opt.param_names!r} must not be a single string"
        )
        opt_space = opt.optimization_space
        shape: t.Optional[tuple[int, ...]] = getattr(opt_space, "shape", None)
        assert shape is not None, (
            f"param names require optimization space with a shape: {opt_space!r}"
        )
        expected = int(np.prod(shape))
        assert len(opt.param_names) == expected, (
            f"expected {expected} parameter names, got {len(opt.param_names)}"
        )
        for param_name in opt.param_names:
            assert isinstance(param_name, str), (
                f"parameter name {param_name!r} must be a string"
            )
    if opt.constraint_names:
        assert not isinstance(opt.constraint_names, str), (
            f"param names {opt.constraint_names!r} must not be a single string"
        )
        expected = len(opt.constraints)
        assert len(opt.constraint_names) == expected, (
            f"expected {expected} parameter names, got {len(opt.constraint_names)}"
        )
        for constraint_name in opt.constraint_names:
            assert isinstance(constraint_name, str), (
                f"constraint name {constraint_name!r} must be a string"
            )


def assert_opt_return_values(opt: SingleOptimizable) -> None:
    """Check the return types of `SingleOptimizable` methods."""
    params = opt.get_initial_params()
    assert params in opt.optimization_space, (
        f"parameters {params} outside of space {opt.optimization_space}"
    )
    assert isinstance(params, np.ndarray), "parameters must be NumPy array"
    params = opt.optimization_space.sample()
    with assert_human_render_called(opt):
        loss = opt.compute_single_objective(params)
    assert is_reward(loss), "loss must be a float or integer"
    assert np.isfinite(float(loss)), f"loss should be finite, not {loss!r}"
