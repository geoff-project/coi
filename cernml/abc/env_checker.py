#!/usr/bin/env python
"""Provides the function `check_env()`."""

import typing as t
import warnings

import gym
import numpy

from .machine import Machine
from .optenv import OptimizeMixin, OptEnv
from .sepenv import SeparableEnv

__all__ = ['check_env']


def check_env(env: OptEnv, warn: bool = True) -> None:
    """Check that an environment follows the restricted API laid out here."""
    assert isinstance(env, gym.Env), \
        f'the environment {type(env)}, must inherit from gym.Env'
    assert isinstance(env, OptimizeMixin), \
        f'the environment {type(env)} must inherit from OptimizeMixin, ' \
        'e.g. via OptEnv'
    assert_observation_space(env)
    assert_action_space(env.action_space)
    assert_optimization_space(env.optimization_space)
    assert_reward_range(env.reward_range)
    assert_returned_values(env)
    assert_no_nan(env)
    if warn:
        if isinstance(env.observation_space, gym.spaces.Box):
            warn_observation_space(env.observation_space)
        elif isinstance(env.observation_space, gym.spaces.Dict):
            warn_observation_space(env.observation_space['observation'])
        warn_render_modes(env)
        warn_machine(env)


def assert_observation_space(env: gym.Env):
    """Check that the observation space is as expected.

    The space must generally be a box. The exception are multi-goal
    environments, which are also allowed to have dict spaces. In this case, the
    dict must have specific keys and the `observation` sub-space must be a box
    in turn.
    """
    space = env.observation_space
    if isinstance(space, gym.spaces.Dict):
        assert isinstance(env, gym.GoalEnv), \
            f'only GoalEnv can have dict observation space {space}'
        actual_keys = set(space.spaces.keys())
        expected_keys = {'observation', 'desired_goal', 'achieved_goal'}
        assert actual_keys == expected_keys, \
            f'GoalEnv observation space must have keys {expected_keys}, ' \
            f'not {actual_keys}'
        assert isinstance(space['observation'], gym.spaces.Box), \
            f'observation space {space["observation"]} must be a ' \
            'gym.spaces.Box'
    else:
        assert isinstance(space, gym.spaces.Box), \
            f'observation space {space} must be a gym.spaces.Box'


def assert_action_space(space: gym.spaces.Box):
    """Check that the given space has symmetric and normalized limits."""
    assert isinstance(space, gym.spaces.Box), \
        f'action space {space} must be a gym.spaces.Box'
    assert numpy.all(abs(space.low) == abs(space.high)), \
        'action space must have symmetric limits'
    assert numpy.any(abs(space.high) <= 1.0), \
        'action space limits must be 1.0 or less'


def assert_optimization_space(space: gym.spaces.Box):
    """Check that the given space is a box."""
    assert isinstance(space, gym.spaces.Box), \
        f'optimization space {space} must be a gym.spaces.Box'


def assert_reward_range(reward_range: t.Tuple[float, float]):
    """Check that the reward range is actually a range."""
    assert len(reward_range) == 2, 'reward range must be tuple `(low, high)`.'
    low, high = reward_range
    assert low <= high, 'lower reward range must be lower than upper bound'


def assert_returned_values(env: gym.Env):
    """Check at `env.rest()` and `env.step()` return the right values."""
    def _check_obs(obs):
        assert obs in env.observation_space, 'observation outside of space'
        inner_obs = obs['observation'] if isinstance(env, gym.GoalEnv) else obs
        assert isinstance(inner_obs, numpy.ndarray), \
            'observation of box space must be NumPy array'

    obs = env.reset()
    _check_obs(obs)
    data = env.step(env.action_space.sample())
    assert len(data) == 4, \
        'step() must return four values: obs, reward, done, info'
    obs, reward, done, info = data
    _check_obs(obs)
    assert isinstance(reward, (float, int, numpy.floating, numpy.integer)), \
        'reward must be a float or integer'
    low, high = env.reward_range
    assert low <= reward <= high, 'reward is out of range'
    assert isinstance(done, bool), 'done signal must be a bool'
    assert isinstance(info, dict), 'info must be a dictionary'
    if isinstance(env, gym.GoalEnv):
        assert reward == env.compute_reward(
            obs['achieved_goal'],
            obs['desired_goal'],
            info,
        ), 'reward does not match'
    elif isinstance(env, SeparableEnv):
        assert reward == env.compute_reward(obs, None, info), \
            'reward does not match'


def assert_no_nan(env: gym.Env):
    """Check that the environment never produces infinity or NaN."""
    def _check_val(val):
        isnan = numpy.any(numpy.isnan(val))
        isinf = numpy.any(numpy.isinf(val))
        return not isnan and not isinf

    obs = env.reset()
    for _ in range(10):
        if isinstance(env, gym.GoalEnv):
            obs = obs['observation']
        assert _check_val(obs), 'observation turned NaN or inf'
        obs, reward, _, _ = env.step(env.action_space.sample())
        assert _check_val(reward), 'reward turned NaN or inf'


def warn_observation_space(space: gym.spaces.Box):
    """Check that the observation space is either flat or an image."""
    ndims = len(space.shape)
    if ndims == 3:
        if space.dtype != numpy.uint8:
            warnings.warn('a 3D tensor observation should be either an image '
                          '(and have dtype uint8), or be flattened into 1D')
        if numpy.any(space.low != 0) or numpy.any(space.high != 255):
            warnings.warn('a 3D tensor observation should be either an image '
                          '(and have bounds [0, 255]), or be flattened into '
                          '1D')
        width, height, _ = space.shape
        if width < 36 or height < 36:
            warnings.warn('an image observation should have at least a '
                          'resolution of 36x36 pixels')
    elif ndims != 1:
        warnings.warn('the observation space has an unconventional shape '
                      '(neither an image nor a 1D vector)')


def warn_render_modes(env: gym.Env):
    """Check that the environment defines the required render modes."""
    render_modes = env.metadata.get('render.modes')
    if render_modes is None:
        warnings.warn('missing key render.modes in the environment metadata')
    if 'ansi' not in render_modes:
        warnings.warn('render mode "ansi" has not been declared in the '
                      'environment metadata')
    if 'qtembed' not in render_modes:
        warnings.warn('render mode "qtembed" has not been declared in the '
                      'environment metadata')


def warn_machine(env: gym.Env):
    """Check that the environment defines the machine it pertains to."""
    machine = env.metadata.get('cern.machine')
    if machine is None:
        warnings.warn('missing key cern.machine in the environment metadata')
    elif not isinstance(machine, Machine):
        warnings.warn('declared cern.machine is not a Machine enum')
