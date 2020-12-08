#!/usr/bin/env python

"""Provide the main entry point check()."""

import typing as t

import gym

from ._problem import Problem, check_problem
from ._single_opt import SingleOptimizable, check_single_optimizable
from ._env import check_env


def check(env: Problem, warn: bool = True) -> None:
    """Check that a problem follows the API of this package."""
    unwrapped_env = getattr(env, "unwrapped", None)
    assert unwrapped_env is not None, f'missing property "unwrapped" on {type(env)}'
    assert isinstance(
        unwrapped_env, Problem
    ), f"{type(unwrapped_env)} must inherit from Problem"
    check_problem(env, warn=warn)
    if isinstance(unwrapped_env, SingleOptimizable):
        check_single_optimizable(t.cast(SingleOptimizable, env), warn=warn)
    if isinstance(unwrapped_env, gym.Env):
        check_env(t.cast(gym.Env, env), warn=warn)
