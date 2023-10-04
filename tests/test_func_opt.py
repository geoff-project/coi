# SPDX-FileCopyrightText: 2020-2024 CERN
# SPDX-FileCopyrightText: 2023-2024 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

"""Test the inheritance chain of the package."""

import numpy as np
from gymnasium.spaces import Box

from cernml import coi


def test_funcopt_defaults() -> None:
    class Subclass(coi.FunctionOptimizable):
        def get_optimization_space(self, cycle_time: float) -> Box:
            return Box(-1, 1, ())

        def get_initial_params(self, cycle_time: float) -> np.ndarray:
            return cycle_time + np.zeros(())

        def compute_function_objective(
            self, cycle_time: float, params: np.ndarray
        ) -> float:
            return np.sum(params) + cycle_time

    problem = Subclass()
    # pylint: disable = assignment-from-none
    # pylint: disable = use-implicit-booleaness-not-comparison
    assert problem.get_objective_function_name() is None
    assert problem.get_param_function_names() == []
    assert problem.override_skeleton_points() is None
