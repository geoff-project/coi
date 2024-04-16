# SPDX-FileCopyrightText: 2020-2024 CERN
# SPDX-FileCopyrightText: 2023-2024 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

"""Minimal example of how to run a `~cernml.coi.FunctionOptimizable`.

This is used by :doc:`/guide/core` and :doc:`/guide/control_flow`.
"""

from fake_module import (  # type: ignore[import-not-found]
    OptFailed,
    get_optimizer,
    request_skeleton_points,
)
from gymnasium.spaces import Box
from numpy import clip

from cernml import coi

problem = coi.make("MyFunctionOptimizableProblem-v0")
assert isinstance(problem, coi.FunctionOptimizable)
with problem:
    # Select skeleton points.
    skeleton_points = problem.override_skeleton_points()
    if skeleton_points is None:
        skeleton_points = request_skeleton_points()

    # Keep track of which points we have modified and which not.
    restore_on_failure = []

    try:
        for time in skeleton_points:
            # Fetch initial state.
            optimizer = get_optimizer()
            space = problem.get_optimization_space(time)
            assert isinstance(space, Box)
            initial = params = problem.get_initial_params(time)
            best = (float("inf"), initial)
            restore_on_failure.append((time, initial))

            while not optimizer.is_done():
                # Update optimum.
                loss = problem.compute_function_objective(time, params)
                best = min(best, (float(loss), params))

                # Fetch next set of parameters.
                params = optimizer.step(loss)
                params = clip(params, space.low, space.high)

            if optimizer.has_failed():
                raise OptFailed(f"optimizer failed at t={time}")
            else:
                # Restore best state.
                problem.compute_function_objective(time, best[1])
    except:
        # If anything fails, restore initial state not only for the
        # current skeleton point, but all previous ones as well.
        while restore_on_failure:
            time, params = restore_on_failure.pop()
            problem.compute_function_objective(time, params)
        raise
