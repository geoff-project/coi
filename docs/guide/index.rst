.. SPDX-FileCopyrightText: 2020 - 2025 CERN
.. SPDX-FileCopyrightText: 2023 - 2025 GSI Helmholtzzentrum für Schwerionenforschung
.. SPDX-FileNotice: All rights not expressly granted are reserved.
..
.. SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

User Guide
==========

The Common Optimization Interfaces make it possible to define optimization
problems in a uniform fashion so that they can be used with as many
optimization algorithms as possible. The goal is to make it possible to write
generic programs that make use of optimization problems written by a third
party without knowing the specifics of the problem.

These interfaces assume a plugin architecture. They assume that an optimization
problem is embedded into some sort of *host* application. As such, the problem
must be able to advertise certain capabilities and properties and the
application must be able to query such properties.

.. toctree::
    :maxdepth: 2

    quickstart
    core
    registration
    custom_optimizers
    configurable
    control_flow
    cancellation
    otherenvs
    funcopt
    migration_090
