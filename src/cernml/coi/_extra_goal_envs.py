# SPDX-FileCopyrightText: 2020-2024 CERN
# SPDX-FileCopyrightText: 2023-2024 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

# pylint: disable = too-many-ancestors

"""These classes provide extra functionality for multi-goal_ environments.

.. _multi-goal: https://robotics.farama.org/content/multi-goal_api/
"""

from __future__ import annotations

import typing as t

from gymnasium.core import ActType, ObsType

from ._classes import ParamType, SingleOptimizable
from ._extra_envs import InfoDict
from ._goalenv import GoalEnv, GoalObs, GoalType
from ._machinery import (
    AttrCheckProtocolMeta,
    get_static_mro,
    non_callable_proto_members,
    proto_hook,
)

__all__ = (
    "ActType",
    "GoalObs",
    "GoalType",
    "InfoDict",
    "ObsType",
    "OptGoalEnv",
    "ParamType",
    "SeparableGoalEnv",
    "SeparableOptGoalEnv",
)


class SeparableGoalEnv(GoalEnv[ObsType, GoalType, ActType]):
    """A multi-goal environment whose calculations nicely separate.

    This interface is superficially similar to `GoalEnv`, but
    additionally also splits out the calculation of the observation and
    the end-of-episode flag. This class differs from `SeparableEnv` in
    the meaning of the parameters that are passed to
    :func:`~gymnasium_robotics.core.GoalEnv.compute_reward()`.

    The split introduced by this class makes two things possible:

    - replacing `compute_observation()` with a function approximator,
      e.g. a neural network;
    - estimating the goodness of the very initial observation of an
      episode via
      :func:`~gymnasium_robotics.core.GoalEnv.compute_reward()`.

    Because of these use cases, all state transition should be
    restricted to `compute_observation()`. In particular, it must be
    possible to call
    :func:`~gymnasium_robotics.core.GoalEnv.compute_reward()`,
    :func:`~gymnasium_robotics.core.GoalEnv.compute_terminated()`, and
    :func:`~gymnasium_robotics.core.GoalEnv.compute_truncated()`
    multiple times without changing the internal state of the
    environment.
    """

    def step(
        self, action: ActType
    ) -> tuple[GoalObs, t.SupportsFloat, bool, bool, InfoDict]:
        """Implementation of :func:`gymnasium.Env.step()`.

        This calls in turn the three new abstract methods:
        `compute_observation()`,
        :func:`~gymnasium_robotics.core.GoalEnv.compute_reward()`,
        :func:`~gymnasium_robotics.core.GoalEnv.compute_terminated()`,
        and
        :func:`~gymnasium_robotics.core.GoalEnv.compute_truncated()`.
        """  # noqa: D402
        info: InfoDict = {}
        obs = self.compute_observation(action, info)
        achieved_goal = t.cast(GoalType, obs["achieved_goal"])
        desired_goal = t.cast(GoalType, obs["desired_goal"])
        reward = self.compute_reward(achieved_goal, desired_goal, info)
        info["reward"] = float(reward)
        terminated = self.compute_terminated(achieved_goal, desired_goal, info)
        truncated = self.compute_truncated(achieved_goal, desired_goal, info)
        return obs, reward, terminated, truncated, info

    def compute_observation(
        self, action: ActType, info: InfoDict
    ) -> GoalObs[ObsType, GoalType]:
        """Compute the next observation if *action* is taken.

        This should encapsulate all state transitions of the
        environment. This means that after any call to
        `compute_observation()`, the other two compute methods can be
        called as often as desired and always give the same results,
        given then the same arguments.

        Args:
            action: the action that was passed to `step()`.
            info: an info dictionary that may be filled with additional
                information.

        Returns:
            The next observation to be returned by `step()`.
        """
        raise NotImplementedError


class OptGoalEnv(
    GoalEnv[ObsType, GoalType, ActType],
    SingleOptimizable[ParamType],
    t.Generic[ObsType, GoalType, ActType, ParamType],
    metaclass=AttrCheckProtocolMeta,
):
    """An optimizable multi-goal environment.

    This is an intersection of `GoalEnv` and `SingleOptimizable`.
    Any class that inherits from both also inherits from this class.
    """

    # Lie about this being a runtime protocol so that `attrs_match()`
    # is run.
    _is_protocol = True
    _is_runtime_protocol = True

    @classmethod
    def __subclasshook__(cls, other: type) -> bool:
        # Our environment base class must be not only implemented by
        # protocol, it must also be in our MRO. Otherwise, SeparableEnv
        # and SeparableGoalEnv would overlap. Preventing this overlap is
        # one of our goals.
        if GoalEnv not in get_static_mro(other):
            return False
        return proto_hook.__get__(None, cls)(other)


# Set `__non_callable_proto_members__` as @runtime_checkable would do on
# Python 3.12+. We can't use @runtime_checkable because this is
# technically not a protocol.
non_callable_proto_members(OptGoalEnv)


class SeparableOptGoalEnv(
    SeparableGoalEnv[ObsType, GoalType, ActType],
    SingleOptimizable[ParamType],
    t.Generic[ObsType, GoalType, ActType, ParamType],
    metaclass=AttrCheckProtocolMeta,
):
    """An optimizable and separable multi-goal environment.

    This is an intersection of `SeparableGoalEnv` and
    `SingleOptimizable`. Any class that inherits from both also inherits
    from this class.
    """

    # Lie about this being a runtime protocol so that `attrs_match()`
    # is run.
    _is_protocol = True
    _is_runtime_protocol = True

    @classmethod
    def __subclasshook__(cls, other: type) -> bool:
        # Our environment base class must be not only implemented by
        # protocol, it must also be in our MRO. Otherwise, SeparableEnv
        # and SeparableGoalEnv would overlap. Preventing this overlap is
        # one of our goals.
        if SeparableGoalEnv not in get_static_mro(other):
            return False
        return proto_hook.__get__(None, cls)(other)


# Set `__non_callable_proto_members__` as @runtime_checkable would do on
# Python 3.12+. We can't use @runtime_checkable because this is
# technically not a protocol.
non_callable_proto_members(SeparableOptGoalEnv)
