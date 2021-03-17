"""Generic assertions and checks used by multiple checkers."""

import numbers
import typing as t

import gym
import numpy as np


def assert_range(reward_range: t.Tuple[float, float], name: str) -> None:
    """Check that the reward range is actually a range."""
    assert len(reward_range) == 2, f"{name} reward range must be tuple `(low, high)`."
    low, high = reward_range
    assert low <= high, f"lower bound of {name} range must be lower than upper bound"


def is_reward(reward: t.Any) -> bool:
    """Return True if the object has the correct type for a reward."""
    return isinstance(reward, (numbers.Number, np.bool_))


def is_box(space: gym.Space) -> bool:
    """Return True if the given space is a Box."""
    return isinstance(space, gym.spaces.Box)
