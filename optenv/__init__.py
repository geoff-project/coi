#!/usr/bin/env python
"""Provides `OptEnv`, which can be used for RL and numerical optimization. """

import gym
import numpy as np


class OptEnv(gym.Env):
    """Interface for optimizable environments.

    An optimizable environment is mostly identical to regular Gym environment,
    but it additionally provides a `step_opt()` method. To describe the bounds
    of valid inputs to it, it also has an attribute `opt_action_space`.
    """
    opt_action_space = None

    def step_opt(self, opt_action):
        """Perform an optimizer step.

        This function is similar to `step()`, but is tuned for numerical
        optimizers. It should not perform a single step through the phase
        space, but instead immediately go to the given point.

        In addition, this function only returns the reward. Other information
        is not necessary.
        """
        raise NotImplementedError()


class Parabola(OptEnv):
    """Example implementation of `OptEnv`.

    The goal of this environment is to find the center of a 2D parabola.
    """
    observation_space = gym.spaces.Box(-np.inf, 0.0, (1, ))
    action_space = gym.spaces.Box(-0.2, 0.2, (2, ))
    opt_action_space = gym.spaces.Box(-1.0, 1.0, (2, ))
    reward_range = (-np.inf, 0.0)

    def __init__(self):
        self.x = np.zeros(2)

    def reset(self):
        self.x = self.opt_action_space.sample()

    def step(self, action):
        new_x = self.x + action
        if new_x in self.opt_action_space:
            self.x = new_x
        obs = sum(self.x**2)
        reward = -obs
        done = obs < 0.01
        return obs, reward, done, {}

    def step_opt(self, opt_action):
        if opt_action in self.opt_action_space:
            self.x = opt_action
        reward = -sum(self.x**2)
        return reward

    def render(self, mode='human'):
        return str(self.x)

    def seed(self, seed=None):
        seeds = self.observation_space.seed(seed)
        seeds.extend(self.action_space.seed(seed))
        seeds.extend(self.opt_action_space.seed(seed))
        return seeds
