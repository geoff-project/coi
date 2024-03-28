..
    SPDX-FileCopyrightText: 2020-2024 CERN
    SPDX-FileCopyrightText: 2023-2024 GSI Helmholtzzentrum für Schwerionenforschung
    SPDX-FileNotice: All rights not expressly granted are reserved.

    SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

Goal-Based Interfaces
=====================

.. automodule:: cernml.coi._extra_goal_envs
    :no-members:

.. currentmodule:: cernml.coi

.. class:: GoalEnv
    :module: cernml.coi

    Bases: `Env`\ [`Any`, `ActType`], `Generic`\ [`ObsType`, `GoalType`, `ActType`]

    This is a vendored copy of :class:`gymrob:gymnasium_robotics.core.GoalEnv`.
    It is only used if the :doc:`gymnasium-robotics <gymrob:README>` package is
    not installed. If it is installed, this is automatically an alias to the
    original class.

.. autoclass:: OptGoalEnv

.. autoclass:: SeparableGoalEnv

.. autoclass:: SeparableOptGoalEnv

.. autoclass:: GoalObs

.. data:: GoalType
    :type: typing.TypeVar

    The generic type variable for the *achieved_goal* and *desired_goal* of
    `GoalEnv`. This is exported for the user's convenience.
