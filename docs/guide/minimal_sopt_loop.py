# SPDX-FileCopyrightText: 2020 - 2024 CERN
# SPDX-FileCopyrightText: 2023 - 2024 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

"""Minimal example of how to run a `~cernml.coi.SingleOptimizable`.

This is used by :doc:`/guide/core` and :doc:`/guide/control_flow`.
"""

from fake_module import get_optimizer  # type: ignore[import-not-found]
from gymnasium.spaces import Box
from numpy import clip

from cernml import coi

problem = coi.make("MySingleOptimizableProblem-v0")
assert isinstance(problem, coi.SingleOptimizable)
with problem:
    # Fetch initial state.
    optimizer = get_optimizer()
    space = problem.optimization_space
    assert isinstance(space, Box)
    initial = params = problem.get_initial_params()
    best = (float("inf"), initial)

    while not optimizer.is_done():
        # Update optimum.
        loss = problem.compute_single_objective(params)
        best = min(best, (float(loss), params))

        # Fetch next set of parameters.
        params = optimizer.step(loss)
        params = clip(params, space.low, space.high)

    if optimizer.has_failed():
        # Restore initial state.
        problem.compute_single_objective(initial)
    else:
        # Restore best state.
        problem.compute_single_objective(best[1])
