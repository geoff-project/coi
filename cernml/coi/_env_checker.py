#!/usr/bin/env python
"""Provides the function `check_env()`."""

import numbers
import typing as t
import warnings

import gym
import numpy
import scipy.optimize

from ._machine import Machine
from ._optenv import Constraint, OptEnv, SingleOptimizable
from ._problem import Problem
from ._sepenv import SeparableEnv


def check(env: OptEnv, warn: bool = True) -> None:
    """Check that an environment follows the restricted API laid out here."""
    unwrapped_env = getattr(env, "unwrapped", None)
    assert unwrapped_env is not None, f'missing property "unwrapped" on {type(env)}'
    assert isinstance(
        unwrapped_env, Problem
    ), f"{type(unwrapped_env)} must inherit from Problem"
    check_problem(env, warn=warn)
    if isinstance(unwrapped_env, SingleOptimizable):
        check_single_optimizable(env, warn=warn)
    if isinstance(unwrapped_env, gym.Env):
        check_env(env, warn=warn)


def check_problem(problem: Problem, warn: bool = True) -> None:
    """Check that a problem follows our conventions."""
    assert_machine(problem)
    if warn:
        warn_render_modes(problem)


def check_single_optimizable(opt: SingleOptimizable, warn: bool = True) -> None:
    """Check that an optimizable follows our conventions."""
    _ = warn  # Flag is currently unused, keep it for forward compatibility.
    assert_optimization_space(opt)
    assert_range(opt.objective_range, "objective")
    assert_constraints(opt.constraints)
    assert_opt_returned_values(opt)


def check_env(env: gym.Env, warn: bool = True) -> None:
    """Check that an environment follows our conventions."""
    assert isinstance(env, gym.Env), f"{type(env)} must inherit from gym.Env"
    assert_observation_space(env)
    assert_action_space(env)
    assert_range(env.reward_range, "reward")
    assert_env_returned_values(env)
    assert_env_no_nan(env)
    if warn:
        if is_box(env.observation_space):
            warn_observation_space(env.observation_space)
        elif isinstance(env.observation_space, gym.spaces.Dict):
            warn_observation_space(env.observation_space["observation"])


def assert_inheritance(env: OptEnv) -> None:
    """Check that the object is an OptEnv."""
    assert isinstance(env, gym.Env), f"{type(env)} must inherit from gym.Env"
    assert isinstance(
        env, SingleOptimizable
    ), f"{type(env)} must inherit from SingleOptimizable"


def assert_observation_space(env: gym.Env) -> None:
    """Check that the observation space is as expected.

    The space must generally be a box. The exception are multi-goal
    environments, which are also allowed to have dict spaces. In this case, the
    dict must have specific keys and the `observation` sub-space must be a box
    in turn.
    """
    space = env.observation_space
    if isinstance(space, gym.spaces.Dict):
        assert isinstance(
            env, gym.GoalEnv
        ), f"only GoalEnv can have dict observation space {space}"
        actual_keys = set(space.spaces.keys())
        expected_keys = {"observation", "desired_goal", "achieved_goal"}
        assert actual_keys == expected_keys, (
            f"GoalEnv observation space must have keys {expected_keys}, "
            f"not {actual_keys}"
        )
        assert is_box(space["observation"]), (
            f'observation space {space["observation"]} must be a ' "gym.spaces.Box"
        )
    else:
        assert is_box(space), f"observation space {space} must be a gym.spaces.Box"


def assert_action_space(env: gym.Env) -> None:
    """Check that the given space has symmetric and normalized limits."""
    space = env.action_space
    assert is_box(space), f"action space {space} must be a gym.spaces.Box"
    assert numpy.all(
        abs(space.low) == abs(space.high)
    ), "action space must have symmetric limits"
    assert numpy.any(abs(space.high) <= 1.0), "action space limits must be 1.0 or less"


def assert_optimization_space(env: SingleOptimizable) -> None:
    """Check that action and optimization space are boxes of the same shape."""
    opt_space = env.optimization_space
    assert is_box(opt_space), f"optimization space {opt_space} must be a gym.spaces.Box"
    if isinstance(env, gym.Env):
        act_space = env.action_space
        assert is_box(act_space), f"action space {act_space} must be a gym.spaces.Box"
        assert act_space.shape == opt_space.shape, (
            f"action {act_space.shape} and optimization {opt_space.shape} space "
            "have the same shape"
        )


def assert_range(reward_range: t.Tuple[float, float], name: str) -> None:
    """Check that the reward range is actually a range."""
    assert len(reward_range) == 2, f"{name} reward range must be tuple `(low, high)`."
    low, high = reward_range
    assert low <= high, f"lower bound of {name} range must be lower than upper bound"


def assert_constraints(constraints: t.List[Constraint]) -> None:
    """Check that the list of constraints contains only constraints."""
    allowed_types = (
        scipy.optimize.LinearConstraint,
        scipy.optimize.NonlinearConstraint,
    )
    for constraint in constraints:
        assert isinstance(constraint, allowed_types), (
            f"constraint {constraint!r} is neither LinearConstraint nor "
            f"NonlinearConstraint"
        )


def assert_opt_returned_values(opt: SingleOptimizable) -> None:
    """Check that the `SingleOptimizable` methods return the right values."""
    params = opt.get_initial_params()
    assert params in opt.optimization_space, "parameters outside of space"
    assert isinstance(params, numpy.ndarray), "parameters must be NumPy array"
    loss = opt.compute_single_objective(opt.optimization_space.sample())
    assert is_reward(loss), "loss must be a float or integer"
    low, high = opt.objective_range
    assert low <= loss <= high, f"loss is out of range [{low}, {high}]: {loss}"


def assert_env_returned_values(env: gym.Env) -> None:
    """Check that `env.rest()` and `env.step()` return the right values."""

    def _check_obs(obs: numpy.ndarray) -> None:
        assert obs in env.observation_space, "observation outside of space"
        inner_obs = obs["observation"] if isinstance(env, gym.GoalEnv) else obs
        assert isinstance(
            inner_obs, numpy.ndarray
        ), "observation of box space must be NumPy array"

    obs = env.reset()
    _check_obs(obs)
    data = env.step(env.action_space.sample())
    assert len(data) == 4, "step() must return four values: obs, reward, done, info"
    obs, reward, done, info = data
    _check_obs(obs)
    assert is_reward(reward), "reward must be a float or integer"
    low, high = env.reward_range
    assert low <= reward <= high, f"reward is out of range [{low}, {high}]: {reward}"
    assert isinstance(done, (bool, numpy.bool_)), f"done signal must be a bool: {done}"
    assert isinstance(info, dict), f"info must be a dictionary: {info}"
    if isinstance(env, gym.GoalEnv):
        assert reward == env.compute_reward(
            obs["achieved_goal"],
            obs["desired_goal"],
            info,
        ), "reward does not match"
    elif isinstance(env, SeparableEnv):
        assert reward == env.compute_reward(obs, None, info), "reward does not match"


def assert_env_no_nan(env: gym.Env) -> None:
    """Check that the environment never produces infinity or NaN."""

    def _check_val(val: t.Union[float, numpy.ndarray, numpy.floating]) -> bool:
        isnan = numpy.any(numpy.isnan(val))
        isinf = numpy.any(numpy.isinf(val))
        return not isnan and not isinf

    obs = env.reset()
    for _ in range(10):
        if isinstance(env, gym.GoalEnv):
            obs = obs["observation"]
        assert _check_val(obs), "observation turned NaN or inf"
        obs, reward, _, _ = env.step(env.action_space.sample())
        assert _check_val(reward), "reward turned NaN or inf"


def assert_machine(env: Problem) -> None:
    """Check that the environment defines the machine it pertains to."""
    machine = env.metadata.get("cern.machine")
    assert machine is not None, "missing key cern.machine in the environment metadata"
    assert isinstance(machine, Machine), "declared cern.machine is not a Machine enum"


def warn_observation_space(space: gym.spaces.Box) -> None:
    """Check that the observation space is either flat or an image."""
    ndims = len(space.shape)
    if ndims == 3:
        if space.dtype != numpy.uint8:
            warnings.warn(
                "a 3D tensor observation should be either an image "
                "(and have dtype uint8), or be flattened into 1D"
            )
        if numpy.any(space.low != 0) or numpy.any(space.high != 255):
            warnings.warn(
                "a 3D tensor observation should be either an image "
                "(and have bounds [0, 255]), or be flattened into 1D"
            )
        width, height, _ = space.shape
        if width < 36 or height < 36:
            warnings.warn(
                "an image observation should have at least a "
                "resolution of 36x36 pixels"
            )
    elif ndims != 1:
        warnings.warn(
            "the observation space has an unconventional shape "
            "(neither an image nor a 1D vector)"
        )


def warn_render_modes(env: Problem) -> None:
    """Check that the environment defines the required render modes."""
    render_modes = env.metadata.get("render.modes")
    if render_modes is None:
        warnings.warn("missing key render.modes in the environment metadata")
    if "ansi" not in render_modes:
        warnings.warn(
            'render mode "ansi" has not been declared in the environment metadata'
        )
    if "qtembed" not in render_modes:
        warnings.warn(
            'render mode "qtembed" has not been declared in the environment metadata'
        )


def is_reward(reward: t.Any) -> bool:
    """Return True if the object has the correct type for a reward."""
    return isinstance(reward, (numbers.Number, numpy.bool_))


def is_box(space: gym.Space) -> bool:
    """Return True if the given space is a Box."""
    return isinstance(space, gym.spaces.Box)
