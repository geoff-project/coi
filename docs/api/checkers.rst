.. SPDX-FileCopyrightText: 2020 - 2024 CERN
.. SPDX-FileCopyrightText: 2023 - 2024 GSI Helmholtzzentrum für Schwerionenforschung
.. SPDX-FileNotice: All rights not expressly granted are reserved.
..
.. SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

Problem Checkers
================

.. automodule:: cernml.coi.checkers
    :no-members:

.. autofunction:: cernml.coi.check

.. autofunction:: check_problem

.. autofunction:: check_single_optimizable

.. autofunction:: check_function_optimizable

.. autofunction:: check_env

.. autofunction:: check_configurable

.. entrypoint:: cernml.checkers

    :doc:`Entry points <pkg:specifications/entry-points>` defined under this
    group allow you to extend the functionality of this package. Each one
    should point at a function using the syntax
    :samp:`{module_name}:{function_name}`. When called, `cernml.coi.check()`
    first runs all built-in checks, then loads all entry points in this group
    and calls each one with the signature :samp:`checker({problem},
    warn={warn}, headless={headless})`.

    The *warn* parameter passed to the entry point is guaranteed to either be
    `False` or an integer ≥ 3. This means that if your checker uses *warn* as
    a *stacklevel* parameter to :func:`warnings.warn()`, the warning will be
    reported from the line where `~cernml.coi.check()` was called. This makes
    it easier to attribute a warning to the correct optimization problem.
