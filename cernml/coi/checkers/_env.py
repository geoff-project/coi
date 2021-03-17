"""Checker for the `gym.Env` ABC."""

import typing as t
import warnings

import gym
import numpy as np

from .._sepenv import SeparableEnv
from ._generic import assert_range, is_box, is_reward


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
    assert np.all(
        abs(space.low) == abs(space.high)
    ), "action space must have symmetric limits"
    assert np.any(abs(space.high) <= 1.0), "action space limits must be 1.0 or less"


def assert_env_returned_values(env: gym.Env) -> None:
    """Check that `env.rest()` and `env.step()` return the right values."""

    def _check_obs(obs: np.ndarray) -> None:
        assert (
            obs in env.observation_space
        ), f"observation {obs} outside of space {env.observation_space}"
        inner_obs = obs["observation"] if isinstance(env, gym.GoalEnv) else obs
        assert isinstance(
            inner_obs, np.ndarray
        ), f"observation {inner_obs} must be NumPy array"

    obs = env.reset()
    _check_obs(obs)
    data = env.step(env.action_space.sample())
    assert (
        len(data) == 4
    ), f"step() must return four values: obs, reward, done, info; not {data}"
    obs, reward, done, info = data
    _check_obs(obs)
    assert is_reward(reward), "reward must be a float or integer"
    low, high = env.reward_range
    assert low <= reward <= high, f"reward is out of range [{low}, {high}]: {reward}"
    assert isinstance(done, (bool, np.bool_)), f"done signal must be a bool: {done}"
    assert isinstance(info, dict), f"info must be a dictionary: {info}"
    if isinstance(env, gym.GoalEnv):
        expected = env.compute_reward(obs["achieved_goal"], obs["desired_goal"], info)
        assert reward == expected, f"reward does not match: {reward} != {expected}"
    elif isinstance(env, SeparableEnv):
        expected = env.compute_reward(obs, None, info)
        assert reward == expected, f"reward does not match: {reward} != {expected}"


def assert_env_no_nan(env: gym.Env) -> None:
    """Check that the environment never produces infinity or NaN."""

    def _check_val(val: t.Union[float, np.ndarray, np.floating]) -> bool:
        isnan = np.any(np.isnan(val))
        isinf = np.any(np.isinf(val))
        return not isnan and not isinf

    obs = env.reset()
    for _ in range(10):
        if isinstance(env, gym.GoalEnv):
            obs = obs["observation"]
        assert _check_val(obs), f"NaN or inf in observation: {obs}"
        obs, reward, _, _ = env.step(env.action_space.sample())
        assert _check_val(reward), f"NaN or inf in reward: {reward}"


def warn_observation_space(space: gym.spaces.Box) -> None:
    """Check that the observation space is either flat or an image."""
    ndims = len(space.shape)
    if ndims == 3:
        if space.dtype != np.uint8:
            warnings.warn(
                "a 3D tensor observation should be either an image "
                "(and have dtype uint8), or be flattened into 1D"
            )
        if np.any(space.low != 0) or np.any(space.high != 255):
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
