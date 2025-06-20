.. SPDX-FileCopyrightText: 2020 - 2025 CERN
.. SPDX-FileCopyrightText: 2023 - 2025 GSI Helmholtzzentrum für Schwerionenforschung
.. SPDX-FileNotice: All rights not expressly granted are reserved.
..
.. SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+
.. SPDX-License-Identifier: MIT AND (GPL-3.0-or-later OR EUPL-1.2+)

Common Optimization Interfaces
==============================

.. automodule:: cernml.coi.protocols
    :no-members:

.. autoclass:: Problem
.. autoclass:: SingleOptimizable
.. autoclass:: FunctionOptimizable

.. class:: Env
    :module: cernml.coi.protocols

    Bases: `Problem`, `Generic`\ [`~.ObsType`, `~.ActType`]

    See `gym:gymnasium.Env`. Re-exported for convenience.

.. autoclass:: HasNpRandom

.. class:: Space
    :module: cernml.coi.protocols
    :no-index:

    Bases: `Generic`\ [`T_co <TypeVar>`]

    See `gym:gymnasium.spaces.Space`. Re-exported for convenience.

.. type:: Constraint
    :canonical: ~scipy.optimize.LinearConstraint | ~scipy.optimize.NonlinearConstraint
    :no-index:

    The type of :ref:`constraints
    <tutorials/implement-singleoptimizable:Constraints>` used by
    `SingleOptimizable <SingleOptimizable.constraints>` and
    `FunctionOptimizable <FunctionOptimizable.constraints>`.

.. type:: InfoDict
    :canonical: dict[str, ~typing.Any]
    :no-index:

    General metadata type. Used by `Problem.metadata`, the *options* parameter
    of `~SingleOptimizable.get_initial_params()`, the *options* parameter of
    `reset() <gymnasium.Env.reset>`, and the *info* return value of `step()
    <gymnasium.Env.step>`.

.. data:: ParamType
    :type: typing.TypeVar

    The generic type variable for `SingleOptimizable`.
    This is exported for the user's convenience.
