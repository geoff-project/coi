# SPDX-FileCopyrightText: 2020-2024 CERN
# SPDX-FileCopyrightText: 2023-2024 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

"""Provides the function `check()` to validate a `Problem`."""

from ._configurable import check_configurable
from ._env import check_env
from ._full_check import check
from ._func_opt import check_function_optimizable
from ._generic import assert_range, is_box, is_reward
from ._problem import check_problem
from ._single_opt import check_single_optimizable

__all__ = [
    "assert_range",
    "check",
    "check_configurable",
    "check_env",
    "check_function_optimizable",
    "check_problem",
    "check_single_optimizable",
    "is_box",
    "is_reward",
]
