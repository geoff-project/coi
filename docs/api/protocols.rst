.. SPDX-FileCopyrightText: 2020 - 2024 CERN
.. SPDX-FileCopyrightText: 2023 - 2024 GSI Helmholtzzentrum für Schwerionenforschung
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

.. autodata:: Constraint

.. autoclass:: InfoDict

.. data:: ParamType
    :type: typing.TypeVar

    The generic type variable for `SingleOptimizable`.
    This is exported for the user's convenience.
