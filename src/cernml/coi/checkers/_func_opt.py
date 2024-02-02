# SPDX-FileCopyrightText: 2020-2024 CERN
# SPDX-FileCopyrightText: 2023-2024 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

"""Checker for the `FunctionOptimizable` ABC."""

import typing as t

from scipy.optimize import LinearConstraint, NonlinearConstraint

from .._func_opt import Constraint, FunctionOptimizable
from ._generic import assert_range, is_box


def check_function_optimizable(opt: FunctionOptimizable, warn: bool = True) -> None:
    """Check the run-time invariants of the given interface."""
    _ = warn  # Flag is currently unused, keep it for forward compatibility.
    assert_optimization_space(opt)
    assert_range(opt.objective_range, "objective")
    assert_constraints(opt.constraints)


def assert_optimization_space(env: FunctionOptimizable) -> None:
    """Check that the optimization space is a box.."""
    opt_space = env.get_optimization_space(0.0)
    assert is_box(opt_space), f"optimization space {opt_space} must be a gym.spaces.Box"


def assert_constraints(constraints: t.List[Constraint]) -> None:
    """Check that the list of constraints contains only constraints."""
    allowed_types = (LinearConstraint, NonlinearConstraint)
    for constraint in constraints:
        assert isinstance(constraint, allowed_types), (
            f"constraint {constraint!r} is neither LinearConstraint nor "
            f"NonlinearConstraint"
        )
