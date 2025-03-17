.. SPDX-FileCopyrightText: 2020 - 2024 CERN
.. SPDX-FileCopyrightText: 2023 - 2024 GSI Helmholtzzentrum für Schwerionenforschung
.. SPDX-FileNotice: All rights not expressly granted are reserved.
..
.. SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

Additional Interfaces
=====================

.. seealso::

    :doc:`/guide/otherenvs`
        User guide page on the topic.

.. currentmodule:: cernml.coi

The interfaces documented here are less commonly used, but may still be useful
in certain circumstances. They are all subclasses of `~gymnasium.Env`. Unlike
the :doc:`classes`, they expect you to subclass them, not just to define the
same methods as them.

    >>> from cernml import coi
    ...
    >>> class MySeparable(coi.SeparableEnv):
    ...     def compute_observation(self, action, info):
    ...         print(f"compute_observation({action!r}, {info!r})")
    ...         return "obs"
    ...
    ...     def compute_reward(self, obs, goal, info):
    ...         print(f"compute_reward({obs!r}, {goal!r}, {info!r})")
    ...         return 0.0
    ...
    ...     def compute_terminated(self, obs, reward, info):
    ...         print(f"compute_terminated({obs!r}, {reward!r}, {info!r})")
    ...         return True
    ...
    ...     def compute_truncated(self, obs, reward, info):
    ...         print(f"compute_truncated({obs!r}, {reward!r}, {info!r})")
    ...         return False
    ...
    >>> env = MySeparable()
    >>> env.step("action")
    compute_observation('action', {})
    compute_reward('obs', None, {})
    compute_terminated('obs', 0.0, {'reward': 0.0})
    compute_truncated('obs', 0.0, {'reward': 0.0})
    ('obs', 0.0, True, False, {'reward': 0.0})

.. module:: cernml.coi._goalenv
.. currentmodule:: cernml.coi
.. class:: GoalEnv
    :module: cernml.coi
    :canonical: cernml.coi._goalenv.GoalEnv

    Bases: `Env`\ [`Any`, `ActType`], `Generic`\ [`ObsType`, `GoalType`, `ActType`]

    This is a vendored copy of :class:`gymrob:gymnasium_robotics.core.GoalEnv`.
    It is only used if the :doc:`gymnasium-robotics <gymrob:README>` package is
    not installed. If it is installed, this is automatically an alias to the
    original class.

.. module:: cernml.coi._sepenv
.. currentmodule:: cernml.coi
.. autoclass:: SeparableEnv
.. autoclass:: SeparableGoalEnv
    :no-members:
    :members: step, compute_observation

.. data:: GoalType
    :type: typing.TypeVar
    :canonical: cernml.coi._goalenv.GoalType

    The generic type variable for the *achieved_goal* and *desired_goal* of
    `GoalEnv`. This is exported for the user's convenience.

.. autoclass:: GoalObs
