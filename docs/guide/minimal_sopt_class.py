# SPDX-FileCopyrightText: 2020 - 2025 CERN
# SPDX-FileCopyrightText: 2023 - 2025 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

"""Minimal example of SingleOptimizable, used by :doc:`/guide/core`."""

import numpy as np
from gymnasium.spaces import Box

from cernml import coi


class Quadratic(coi.SingleOptimizable):
    # This class doesn't do any rendering, but it's still useful to pass
    # this parameter on, in case, you want to add rendering later.
    def __init__(self, render_mode=None):
        # The inherited initializer checks for us that `render_mode` is
        # valid, and saves it as `self.render_mode`.
        super().__init__(render_mode)

        # Here, we define our problem's domain. Since the space is
        # constant, we could've defined `optimization_space = Box(...)`
        # at class scope as well.
        self.optimization_space = Box(-1.0, 1.0, shape=(5,))

        # The goal to be found by the optimizer. Randomized on each call
        # to `get_initial_params()`.
        self.goal = np.zeros(5)

    # Defining the x_0 for our optimization problem. `seed` allows
    # fixing random-number generation (RNG), `options` is a free-form
    # dict that we can use for customization.
    def get_initial_params(self, *, seed=None, options=None):
        # The inherited function seeds an RNG `self.np_random` for us.
        super().get_initial_params(seed=seed)

        # We bind these attributes here to keep our code short.
        space = self.optimization_space
        rng = self.np_random

        # Randomize the goal we want to move to and the initial point.
        # We use `np_random` so that if the user passes `seed`, the
        # problem is completely deterministic.
        self.goal = rng.uniform(space.low, space.high, size=space.shape)
        return rng.uniform(space.low, space.high, size=space.shape)

    # Our objective function is simply the RMS of the distance between
    # the two points.
    def compute_single_objective(self, params):
        return np.linalg.norm(self.goal - params)


# Never forget to register your optimization problem!
coi.register("QuadraticSearch-v1", entry_point=Quadratic)
