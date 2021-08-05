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


def assert_opt_returned_values(opt: SingleOptimizable) -> None:
    """Check the return types of `SingleOptimizable` methods."""
    params = opt.get_initial_params()
    assert params in opt.optimization_space, "parameters outside of space"
    assert isinstance(params, np.ndarray), "parameters must be NumPy array"
    loss = opt.compute_single_objective(opt.optimization_space.sample())
    assert is_reward(loss), "loss must be a float or integer"
    low, high = opt.objective_range
    assert low <= loss <= high, f"loss is out of range [{low}, {high}]: {loss}"
