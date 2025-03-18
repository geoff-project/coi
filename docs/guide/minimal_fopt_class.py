# SPDX-FileCopyrightText: 2020 - 2025 CERN
# SPDX-FileCopyrightText: 2023 - 2025 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

"""Minimal example of FunctionOptimizable, used by :doc:`/guide/core`."""

import numpy as np
from gymnasium.spaces import Box

from cernml import coi


class StraightLineSteering(coi.FunctionOptimizable):
    # This class doesn't do any rendering, but it's still useful to pass
    # this parameter on, in case, you want to add rendering later.
    def __init__(self, render_mode=None):
        # The inherited initializer checks for us that `render_mode` is
        # valid, and saves it as `self.render_mode`.
        super().__init__(render_mode)

        # Our problem has a number of disturbances, initialized in
        # `get_initial_params()`. Each one deviates our trajectory
        # either to the left (negative values) or to the right (positive
        # values). Our goal is to keep the trajectory as close to zero
        # as possible.
        self.disturbances = {}

    # Our problem is particularly simple and has the same optimization
    # space everywhere.
    def get_optimization_space(self, cycle_time):
        return Box(-1, 1, shape=())

    # Defining the x_0 for our optimization problem. `seed` allows
    # fixing random-number generation (RNG), `options` is a free-form
    # dict that we can use for customization.
    def get_initial_params(self, cycle_time, *, seed=None, options=None):
        # The inherited function seeds an RNG `self.np_random` for us.
        super().get_initial_params(cycle_time, seed=seed)

        # Check that the given cycle time is allowed.
        if not 0.0 < cycle_time < 1500.0:
            raise ValueError(f"cycle time out of bounds: {cycle_time!r}")

        # Initialize the disturbances here. We want the RNG to have been
        # seeded already.
        if not self.disturbances:
            self.disturbances = {
                self.np_random.integers(0, 1500): self.np_random.normal()
                for _ in range(3)
            }

        return np.array(self.disturbances.get(int(cycle_time), 0.0))

    # Our objective function is the integrated deviation from the ideal
    # trajectory. Because each segment is a straight line, we simply
    # calculate according to the trapezoidal rule.
    def compute_function_objective(self, cycle_time, params):
        # Apply the given parameters.
        self.disturbances[int(cycle_time)] = float(params.item())
        # Calculate the loss function by iterating over all disturbances
        # in order.
        integral = 0.0
        prev_time = 0.0
        prev_pos = 0.0
        trajectory = 0.0
        for time, disturbance in sorted(self.disturbances.items()):
            pos = trajectory * (time - prev_time)
            integral += 0.5 * (pos + prev_pos) * (time - prev_time)
            trajectory += disturbance
            prev_time = time
            prev_pos = pos
        time = 1500
        pos = trajectory * (time - prev_time)
        integral += 0.5 * (pos + prev_pos) * (time - prev_time)
        # Cost function is the square because negative deviations are
        # just as bad as positive ones.
        return integral**2


# Never forget to register your optimization problem!
coi.register("StraightLineSteering-v1", entry_point=StraightLineSteering)
