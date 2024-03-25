# SPDX-FileCopyrightText: 2020-2024 CERN
# SPDX-FileCopyrightText: 2023-2024 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

# pylint: disable = too-many-ancestors

"""Interfaces that combine two or more base interfaces."""

from __future__ import annotations

import sys
import typing as t
from abc import ABCMeta

from gymnasium.core import ActType, ObsType

from ._extra_envs import InfoDict
from ._goalenv import GoalEnv, GoalType
from ._single_opt import ParamType, SingleOptimizable

if sys.version_info < (3, 11):
    from typing_extensions import TypedDict
else:
    from typing import TypedDict

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


class GoalObs(TypedDict, t.Generic[ObsType, GoalType]):
    """Type annotation for the observation type of `.GoalEnv`."""

    observation: ObsType
    desired_goal: GoalType
    achieved_goal: GoalType


class SeparableGoalEnv(GoalEnv[ObsType, GoalType, ActType]):
    """A multi-goal environment whose calculations nicely separate.

    This interface is superficially similar to `~gym.GoalEnv`, but
    additionally also splits out the calculation of the observation and
    the end-of-episode flag. This class differs from `SeparableEnv` in
    the meaning of the parameters that are passed to
    `~gym.GoalEnv.compute_reward()`.

    The split introduced by this class makes two things possible:

    - replacing `compute_observation()` with a function approximator,
      e.g. a neural network;
    - estimating the goodness of the very initial observation of an
      episode via `~gym.GoalEnv.compute_reward()`.

    Because of these use cases, all state transition should be
    restricted to `compute_observation()`. In particular, it must be
    possible to call `gym.GoalEnv.compute_reward()` and `compute_done()`
    multiple times without changing the internal state of the
    environment.
    """

    def step(
        self, action: ActType
    ) -> tuple[dict[str, ObsType | GoalType], t.SupportsFloat, bool, bool, InfoDict]:
        """Implementation of `gym.Env.step()`.

        This calls in turn the three new abstract methods:
        `compute_observation()`, `~gym.GoalEnv.compute_reward()`,
        `compute_terminated()` and `compute_truncated()`.
        """  # noqa: D402
        info: InfoDict = {}
        obs = t.cast(
            dict[str, t.Union[ObsType, GoalType]],
            self.compute_observation(action, info),
        )
        achieved_goal = t.cast(GoalType, obs["achieved_goal"])
        desired_goal = t.cast(GoalType, obs["desired_goal"])
        reward = self.compute_reward(achieved_goal, desired_goal, info)
        info["reward"] = reward
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
    metaclass=ABCMeta,
):
    """An optimizable multi-goal environment.

    This is an intersection of `~gym.GoalEnv` and `SingleOptimizable`.
    Any class that inherits from both, also inherits from this class.
    """

    @classmethod
    def __subclasshook__(cls, other: type) -> bool:
        # Circumvent `issubclass()` to prevent recursion;
        # ABC.__subclasscheck__ goes through _every_ subclass of an ABC.
        proto = SingleOptimizable.__subclasshook__(other)
        if issubclass(other, GoalEnv) and proto is True:
            return True
        return NotImplemented


class SeparableOptGoalEnv(
    SeparableGoalEnv[ObsType, GoalType, ActType],
    SingleOptimizable[ParamType],
    t.Generic[ObsType, GoalType, ActType, ParamType],
    metaclass=ABCMeta,
):
    """An optimizable and separable multi-goal environment.

    This is an intersection of `SeparableGoalEnv` and
    `SingleOptimizable`. Any class that inherits from both, also
    inherits from this class.
    """

    @classmethod
    def __subclasshook__(cls, other: type) -> bool:
        # Circumvent `issubclass()` to prevent recursion;
        # ABC.__subclasscheck__ goes through _every_ subclass of an ABC.
        proto = SingleOptimizable.__subclasshook__(other)
        if issubclass(other, SeparableGoalEnv) and proto is True:
            return True
        return NotImplemented
