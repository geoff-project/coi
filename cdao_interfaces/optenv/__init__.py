#!/usr/bin/env python
"""Provides `OptEnv`, which can be used for RL and numerical optimization. """

import gym


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
