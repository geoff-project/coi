# SPDX-FileCopyrightText: 2020-2024 CERN
# SPDX-FileCopyrightText: 2023-2024 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

"""Checker for the `gymnasium.Env` ABC."""

import warnings

import numpy as np
from gymnasium import Env, spaces

from .._typeguards import is_env, is_goal_env, is_separable_env
from ._generic import assert_range, bump_warn_arg, is_bool, is_box, is_reward


def check_env(env: Env, warn: int = True) -> None:
    """Check the run-time invariants of the given interface."""
    assert is_env(env), f"{type(env)} must inherit from gymnasium.Env"
    assert_observation_space(env)
    assert_action_space(env)
    assert_range(env.reward_range, "reward")
    assert_env_returned_values(env)
    assert_env_no_nan(env)
    if warn:
        warn_observation_space(
            env.observation_space,
            warn=bump_warn_arg(warn),
        )


def assert_observation_space(env: Env) -> None:
    """Check that the observation space is as expected.

    The space must generally be a box. The exception are multi-goal
    environments, which are also allowed to have dict spaces. In this
    case, the dict must have specific keys and the `observation`
    sub-space must be a box in turn.
    """
    space = env.observation_space
    if isinstance(space, spaces.Dict):
        assert is_goal_env(env), f"only GoalEnv can have dict observation space {space}"
        actual_keys = set(space.spaces.keys())
        expected_keys = {"observation", "desired_goal", "achieved_goal"}
        assert actual_keys == expected_keys, (
            f"GoalEnv observation space must have keys {expected_keys}, "
            f"not {actual_keys}"
        )
        assert is_box(
            space["observation"]
        ), f'observation space {space["observation"]} must be a gym.spaces.Box'
    else:
        assert is_box(space), f"observation space {space} must be a gym.spaces.Box"


def assert_action_space(env: Env) -> None:
    """Check that the action space has symmetric/normalized limits."""
    space = env.action_space
    assert is_box(space), f"action space {space} must be a gym.spaces.Box"
    assert np.all(
        abs(space.low) == abs(space.high)
    ), "action space must have symmetric limits"
    assert np.any(abs(space.high) <= 1.0), "action space limits must be 1.0 or less"


def assert_env_returned_values(env: Env) -> None:
    """Check the return types of `env.reset()` and `env.step()`.

    Example:
        >>> class Foo:
        ...     reward_range = (-1.0, 1.0)
        ...     observation_space = spaces.Box(-1, 1, ())
        ...     action_space = observation_space
        ...     @property
        ...     def unwrapped(self):
        ...         return self
        ...     def reset(self, seed=None, options=None):
        ...         return np.array(0.0, dtype=np.float32), {}
        ...     def step(self, action):
        ...         return action, 0.0, False, False, {}
        >>> assert_env_returned_values(Foo())
    """

    def _check_obs(obs: np.ndarray) -> None:
        assert (
            obs in env.observation_space
        ), f"observation {obs} outside of space {env.observation_space}"
        inner_obs = obs["observation"] if is_goal_env(env) else obs
        assert isinstance(
            inner_obs, np.ndarray
        ), f"observation {inner_obs} must be NumPy array"

    obs, info = env.reset()
    _check_obs(obs)
    assert isinstance(
        info, dict
    ), f"`info` returned by `reset()` must be a dictionary: {info}"
    data = env.step(env.action_space.sample())
    assert len(data) == 5, (
        f"step() must return four values: obs, reward, "
        f"terminated, truncated, info; not {data}"
    )
    obs, reward, terminated, truncated, info = data
    _check_obs(obs)
    assert is_reward(reward), "reward must be a float or integer"
    low, high = env.reward_range
    assert is_reward(low), "reward range must be float: {low!r}"
    assert is_reward(high), "reward range must be float: {high!r}"
    assert (
        float(low) <= float(reward) <= float(high)
    ), f"reward is out of range [{low}, {high}]: {reward!r}"
    assert is_bool(terminated), f"`terminated` signal must be a bool: {terminated!r}"
    assert is_bool(truncated), f"`truncated` signal must be a bool: {truncated!r}"
    assert isinstance(
        info, dict
    ), f"`info` returned by `step()` must be a dictionary: {info}"
    if is_goal_env(env):
        expected = env.compute_reward(obs["achieved_goal"], obs["desired_goal"], info)
        assert reward == expected, f"reward does not match: {reward} != {expected}"
    elif is_separable_env(env):
        expected = env.compute_reward(obs, None, info)
        assert reward == expected, f"reward does not match: {reward} != {expected}"


def assert_env_no_nan(env: Env) -> None:
    """Check that the environment never produces infinity or NaN."""
    terminated = truncated = True
    for _ in range(10):
        if terminated or truncated:
            obs, _ = env.reset()
        if is_goal_env(env):
            obs = obs["observation"]
        assert np.all(np.isfinite(obs)), f"NaN or inf in observation: {obs}"
        obs, reward, terminated, truncated, _ = env.step(env.action_space.sample())
        assert np.isfinite(float(reward)), f"NaN or inf in reward: {reward}"


def warn_observation_space(space: spaces.Space, warn: int = True) -> None:
    """Check that the observation space has the right shape.

    For a regular `.Env`, the space must be a `Box` with either a flat
    shape, or the shape of a pixel array (dtype is `~numpy.uint8`, shape
    is 3D ``(width, height, channels)``, values go from 0 to 255
    inclusive, image is at least 36 pixels wide and high).

    For a `.GoalEnv`, the space must be a `Dict` with the keys expected
    by the API. The ``"observation"`` sub-space must be a `Box` with the
    same requirements as above.
    """
    warn = bump_warn_arg(warn)
    if is_box(space):
        warn_flat_observation_space(space, warn=warn)
        return
    assert isinstance(space, spaces.Dict), (
        f"for now, observation spaces must be Box or "
        f"(for GoalEnv) Dict, not {space!r}"
    )
    nested_space = space.get("observation")
    assert (
        nested_space is not None
    ), f"Dict space is missing required key 'observation': {space!r}"
    assert is_box(
        nested_space
    ), f"observation_space['observation'] is not a Box: {nested_space!r}"
    warn_flat_observation_space(nested_space, warn=warn)


def warn_flat_observation_space(space: spaces.Box, warn: int = True) -> None:
    """Check that the observation space is either flat or an image.

    Examples:

        >>> from warnings import simplefilter
        >>> from gymnasium.spaces import Box
        >>> simplefilter("error")
        >>> warn_observation_space(Box(-1, 1, (10,)))
        >>> warn_observation_space(Box(-1, 1, (10, 10)))
        Traceback (most recent call last):
        ...
        UserWarning: ... an unconventional shape ...
        >>> warn_observation_space(Box(-1, 1, (10, 10, 10)))
        Traceback (most recent call last):
        ...
        UserWarning: ... (and have dtype uint8), or ...
        >>> warn_observation_space(Box(0, 1, (10, 10, 10), np.uint8))
        Traceback (most recent call last):
        ...
        UserWarning: ... (and have bounds [0, 255]), or ...
        >>> warn_observation_space(Box(0, 255, (10, 10, 10), np.uint8))
        Traceback (most recent call last):
        ...
        UserWarning: ... at least a resolution of 36x36 pixels
        >>> warn_observation_space(Box(0, 255, (36, 36, 10), np.uint8))
    """
    if not warn:
        return
    ndims = len(space.shape)
    if ndims == 3:
        if space.dtype != np.uint8:
            warnings.warn(
                "a 3D tensor observation should be either an image "
                "(and have dtype uint8), or be flattened into 1D",
                stacklevel=max(2, warn),
            )
        if np.any(space.low != 0) or np.any(space.high != 255):
            warnings.warn(
                "a 3D tensor observation should be either an image "
                "(and have bounds [0, 255]), or be flattened into 1D",
                stacklevel=max(2, warn),
            )
        width, height, _ = space.shape
        if width < 36 or height < 36:
            warnings.warn(
                "an image observation should have at least a "
                "resolution of 36x36 pixels",
                stacklevel=max(2, warn),
            )
    elif ndims != 1:
        warnings.warn(
            "the observation space has an unconventional shape "
            "(neither an image nor a 1D vector)",
            stacklevel=max(2, warn),
        )
