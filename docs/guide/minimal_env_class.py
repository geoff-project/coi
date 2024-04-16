# SPDX-FileCopyrightText: 2020-2024 CERN
# SPDX-FileCopyrightText: 2023-2024 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

"""Minimal example of Env, used by :doc:`/guide/core`."""

import numpy as np
from gymnasium import Env
from gymnasium.spaces import Box

from cernml import coi


class Quadratic(Env):
    # This class doesn't do any rendering, but it's still useful to
    # accept this parameter, in case, you want to add rendering later.
    def __init__(self, render_mode=None):
        # The `render_mode` attribute is defined by `Env`.
        self.render_mode = render_mode

        # Here, we define our problem's domain. The observations that we
        # receive are 2×5 arrays containing the goal and the current
        # position …
        self.observation_space = Box(-5.0, 5.0, shape=(2, 5))

        # … and the actions are 5D arrays containing the direction where
        # to walk on each step.
        self.action_space = Box(-1.0, 1.0, shape=(5,))

        # The environment state is the position where we are, and the
        # goal where we should go.
        self.position = np.zeros(5)
        self.goal = np.zeros(5)

    # Defining the initial state for each episode. `seed` allows fixing
    # random-number generation (RNG), `options` is a free-form dict that
    # we can use for customization.
    def reset(self, *, seed=None, options=None):
        # The inherited function seeds an RNG `self.np_random` for us.
        super().reset(seed=seed)

        # We bind these attributes here to keep our code short.
        rng = self.np_random
        space = self.observation_space

        # Randomize the goal we want to move to and the initial point.
        # We use `np_random` so that if the user passes `seed`, the
        # problem is completely deterministic.
        self.goal = rng.uniform(space.low, space.high, size=space.shape)
        self.position = rng.uniform(space.low, space.high, size=space.shape)

        # `Env` expects us to return `obs` (with the shape and limits
        # given by `observation_space`) and a free-form *info* dict,
        # which may contain metrics or debugging or logging info.
        obs = np.stack((self.goal, self.position))
        info = {}
        return obs, info

    # The state transition function. Accepts an action and returns
    # a 5-tuple of: observation, reward for this step, boolean flags
    # that indicate whether the episode is over, and an info dict like
    # in `reset()`.
    def step(self, action):
        # Update our internal state and ensure everything stays within
        # its limits.
        self.position += action
        self.position = np.clip(
            self.position,
            self.observation_space.low[1],
            self.observation_space.high[1],
        )

        # We use the negative distance from the goal as reward. (Higher
        # rewards are better, unlike with `SingleOptimizable`.) We end
        # the episode when sufficiently close to the goal.
        distance = np.linalg.norm(self.goal - self.position)
        obs = np.stack((self.goal, self.position))
        reward = -distance
        terminated = distance < 0.01
        truncated = False
        info = {}
        return obs, reward, terminated, truncated, info


# Never forget to register your optimization problem!
coi.register("QuadraticSearch-v2", entry_point=Quadratic)
