# SPDX-FileCopyrightText: 2020 - 2025 CERN
# SPDX-FileCopyrightText: 2023 - 2025 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

"""These functions help validate your `~.coi.Problem` for API conformity.

The core of this package is `cernml.coi.check()`. It tests which
interfaces your problem implements and automatically calls the correct
specialized checkers. can also be extended with additional checks using
:ep:`cernml.checkers` entry points.

You can also invoke the individual checkers yourself, see e.g.
`check_problem()`.
"""

from ._configurable import check_configurable
from ._env import check_env
from ._full_check import check
from ._func_opt import check_function_optimizable
from ._problem import check_problem
from ._single_opt import check_single_optimizable

__all__ = (
    "check",
    "check_configurable",
    "check_env",
    "check_function_optimizable",
    "check_problem",
    "check_single_optimizable",
)
