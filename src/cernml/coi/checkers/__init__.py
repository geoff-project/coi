# SPDX-FileCopyrightText: 2020-2024 CERN
# SPDX-FileCopyrightText: 2023-2024 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

"""These functions help validate your `~.coi.Problem` for API conformity.

The central entry point for this package is `cernml.coi.check()`. It
tests which interfaces your problem implements and automatically calls
the correct specialized checkers. You can also invoke these checkers
youself with `check_env()`, etc.

The generic `.check()` function also provides a plugin interface via the
:ref:`entry point <setuptools:dynamic discovery of services and
plugins>` ``"cernml.checkers"``. This means that other packages may
provide additional checkers. Upon each call, this method will load all
plugins and call each of them with the signature
:samp:`checker({problem}, warn={warn}, headless={headless})`.
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
