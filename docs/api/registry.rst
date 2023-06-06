..
    SPDX-FileCopyrightText: 2020-2023 CERN
    SPDX-FileCopyrightText: 2023 GSI Helmholtzzentrum für Schwerionenforschung
    SPDX-FileNotice: All rights not expressly granted are reserved.

    SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

The Problem Registry
====================

.. autofunction:: cernml.coi.register

.. autofunction:: cernml.coi.make

.. autofunction:: cernml.coi.spec

.. autodata:: cernml.coi.registry

.. autoclass:: gym.envs.registration.EnvRegistry
   :members:
   :show-inheritance:

.. autoclass:: gym.envs.registration.EnvSpec
   :members:
   :show-inheritance:

.. class:: gym.wrappers.TimeLimit(env, max_episode_steps=None)

   Bases: `gym.Wrapper`

   A standard wrapper around `~gym.Env`. If *max_episode_steps* is passed, it
   truncates each episode to this number of steps.

   You can tell whether an
   episode was truncated or ended naturally by inspecting the *info* dict
   returned by `~gym.Env.step()`:

   - if it contains a key ``"TimeLimit.truncated"`` whose value is True, the
     episode was truncated;
   - if it contains a key ``"TimeLimit.truncated"`` whose value is False, the
     episode ended naturally at exactly the time limit;
   - if if does not contain a key ``"TimeLimit.truncated"``, the episode is
     either still going or ended before reaching the time limit.

   Thus, you can check for truncation like this:

        >>> obs, reward, done, info = env.step(action)
        >>> if info.get("TimeLimit.truncated"):
        ...     print("truncated!")

.. autoexception:: gym.error.Error

   The exception type raised by `~cernml.coi.make()` and `~cernml.coi.spec()`
   if an optimization problem cannot be found in the registry.
