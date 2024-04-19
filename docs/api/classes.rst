..
    SPDX-FileCopyrightText: 2020-2024 CERN
    SPDX-FileCopyrightText: 2023-2024 GSI Helmholtzzentrum für Schwerionenforschung
    SPDX-FileNotice: All rights not expressly granted are reserved.

    SPDX-License-Identifier: MIT AND (GPL-3.0-or-later OR EUPL-1.2+)

:tocdepth: 3

Core Classes of This Package
============================

.. seealso::

    :doc:`/guide/core`
        User guide page on most classes introduced here.
    :doc:`/guide/control_flow`
        User guide page on the order in which the methods introduced here are
        expected to be called.
    :doc:`/guide/custom_optimizers`
        User guide page on specifically `~cernml.coi.CustomOptimizerProvider`.
    :doc:`/guide/funcopt`
        User guide page on specifically `~cernml.coi.FunctionOptimizable`.

.. automodule:: cernml.coi._classes
    :no-members:

.. currentmodule:: cernml.coi

.. autoclass:: Problem
    :inherited-members:

.. autoclass:: SingleOptimizable

.. autoclass:: FunctionOptimizable

.. class:: Env
    :module: cernml.coi

    Bases: `Problem`, `Generic`\ [`ObsType`, `ActType`]

    See `gymnasium.Env`. This is re-exported for the user's convenience.

.. module:: cernml.coi._custom_optimizer_provider
.. currentmodule:: cernml.coi
.. autoclass:: CustomOptimizerProvider

.. autoclass:: CustomPolicyProvider

.. autoclass:: Policy

.. autoclass:: HasNpRandom

Supporting Types
----------------

The following types are not interfaces themselves, but are used by the core
interfaces of this package.

.. module:: cernml.coi._machine
.. currentmodule:: cernml.coi
.. autoclass:: Machine
    :undoc-members:

.. class:: Space
    :module: cernml.coi

    Bases: `Generic`\ [`T_co <TypeVar>`]

    See `gym:gymnasium.spaces.Space`. This is re-exported for the user's
    convenience.

.. autodata:: Constraint

.. data:: ParamType
    :type: typing.TypeVar

    The generic type variable for `SingleOptimizable`.
    This is exported for the user's convenience.

.. data:: ActType
    :type: typing.TypeVar

    The generic type variable for the actions of `~gymnasium.Env` and its
    subclasses. Reexported from Gymnasium for the user's convenience.

.. data:: ObsType
    :type: typing.TypeVar

    The generic type variable for the observables of `~gymnasium.Env` and its
    subclasses. Reexported from Gymnasium for the user's convenience.
