# SPDX-FileCopyrightText: 2020-2024 CERN
# SPDX-FileCopyrightText: 2023-2024 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

"""These are subclasses of `~gymnasium.Env` that separate their calculations."""

from __future__ import annotations

import sys
import typing as t
from abc import abstractmethod

from gymnasium.core import ActType, Env, ObsType

from ._goalenv import GoalEnv, GoalObs, GoalType

if sys.version_info < (3, 12):
    from typing_extensions import override
else:
    from typing import override

__all__ = (
    "ActType",
    "InfoDict",
    "ObsType",
    "GoalType",
    "GoalObs",
    "SeparableEnv",
    "SeparableGoalEnv",
)

InfoDict = dict[str, t.Any]


class SeparableEnv(Env[ObsType, ActType]):
    """An environment whose calculations nicely separate.

    This interface is superficially similar to `GoalEnv`, but doesn't
    pose any requirements to the observation space. (By contrast,
    `.GoalEnv` requires that the observation space is a dict with keys
    ``"observation"``, ``"desired_goal"`` and ``"achieved_goal"``.) The
    only requirement is that the calculation of observation, reward and
    end-of-episode can be separated into distinct steps.

    This makes two things possible:

    - replacing `compute_observation()` with a function approximator,
      e.g. a neural network;
    - estimating the goodness of the very initial observation of an
      episode via :samp:`{env}.compute_reward({env}.reset(), None, {})`.

    Because of these use cases, all state transition should be
    restricted to `compute_observation()`. In particular, it must be
    possible to call `compute_reward()`, `compute_terminated()` and
    `compute_truncated()` multiple times without changing the internal
    state of the environment.
    """

    @override
    def step(
        self, action: ActType
    ) -> tuple[ObsType, t.SupportsFloat, bool, bool, InfoDict]:
        """Implementation of :func:`gymnasium.Env.step()`.

        This calls in turn the four new abstract methods:
        `compute_observation()`, `compute_reward()`,
        `compute_terminated()` and `compute_truncated()`.
        """  # noqa: D402
        info: InfoDict = {}
        obs = self.compute_observation(action, info)
        reward = self.compute_reward(obs, None, info)
        info["reward"] = freward = float(reward)
        terminated = self.compute_terminated(obs, freward, info)
        truncated = self.compute_truncated(obs, freward, info)
        return obs, reward, terminated, truncated, info

    @abstractmethod
    def compute_observation(self, action: ActType, info: InfoDict) -> ObsType:
        """Apply the given *action* and return the next observation.

        This should encapsulate all state transitions of the
        environment. This means that after any call to
        `compute_observation()`, the other two compute methods can be
        called as often as desired and always give the same results,
        given then the same arguments.

        Args:
            action: the action that was passed to `step()`.
            info: an info dictionary that may be filled with
                additional information.

        Returns:
            The next observation to be returned by `step()`.
        """
        raise NotImplementedError

    @abstractmethod
    def compute_reward(
        self, obs: ObsType, goal: None, info: InfoDict
    ) -> t.SupportsFloat:
        """Calculate the reward for the given observation and current state.

        This externalizes the reward function. In this regard, it is
        similar to
        :func:`~gymnasium_robotics.core.GoalEnv.compute_reward()`, but
        it doesn't impose any structure on the observation space.

        Note that this function should be free of side-effects or
        modifications of *self*. In particular, the user is allowed to
        do multiple calls to ``env.compute_reward(obs, None, {})`` and
        always expect the same result.

        Args:
            obs: The observation calculated by
                :func:`~gymnasium.Env.reset()` or
                `compute_observation()`.
            goal: A dummy parameter to stay compatible with the
                `GoalEnv` API. This parameter generally is None. If you
                want a multi-goal environment, consider
                `SeparableGoalEnv`.
            info: an info dictionary with additional information.
                It may or may not have been passed to
                `compute_observation()` before.

        Returns:
            The reward that corresponds to the given observation. This
            value is returned by `step()`.
        """
        raise NotImplementedError

    @abstractmethod
    def compute_terminated(self, obs: ObsType, reward: float, info: InfoDict) -> bool:
        """Compute whether the episode ends in this step.

        This externalizes the decision whether the agent has reached the
        terminal state of the environment (e.g. winning or losing
        a game). This function should be free of side-effects or
        modifications of *self*. In particular, it must be possible to
        call ``env.compute_terminated(obs, reward, {})`` multiple times
        and always get the same result.

        If you want to indicate that the episode has ended in a success,
        consider setting ``info["success"] = True``.

        Args:
            obs: The observation calculated by
                :func:`~gymnasium.Env.reset()` or
                `compute_observation()`.
            reward: The return value of `compute_reward()`.
            info: an info dictionary with additional information. It may
                or may not have been passed to `compute_reward()`
                before. The `step()` method adds a key ``"reward"`` that
                contains the result of `compute_reward()`.

        Returns:
            True if the episode has reached a terminal state, False
            otherwise.
        """
        raise NotImplementedError

    @abstractmethod
    def compute_truncated(self, obs: ObsType, reward: float, info: InfoDict) -> bool:
        """Compute whether the episode ends in this step.

        This externalizes the decision whether a condition outside of
        the environment has ended the episode (e.g. a time limit). This
        function should be free of side-effects or modifications of
        *self*. In particular, it must be possible to call
        ``env.compute_truncated(obs, reward, {})`` multiple times and
        always get the same result.

        Args:
            obs: The observation calculated by
                :func:`~gymnasium.Env.reset()` or
                `compute_observation()`.
            reward: The return value of `compute_reward()`.
            info: an info dictionary with additional information. It may
                or may not have been passed to `compute_reward()`
                before. The `step()` method adds a key ``"reward"`` that
                contains the result of `compute_reward()`.

        Returns:
            True if the episode has been terminated by outside forces,
            False otherwise.
        """
        raise NotImplementedError


# We'd like to say `GoalEnv[ObsType, GoalType, ActType]` here, but
# `gymnasium_robotics.GoalEnv` is not generic.
class SeparableGoalEnv(GoalEnv, t.Generic[ObsType, GoalType, ActType]):
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

    @override
    def step(
        self, action: ActType
    ) -> tuple[GoalObs, t.SupportsFloat, bool, bool, InfoDict]:
        """Implementation of :func:`gymnasium.Env.step()`.

        This calls in turn the four new abstract methods:
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

    @abstractmethod
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

    # Repeat GoalEnv methods here so that they get type annotations even
    # if `gymnasium_robotics.GoalEnv` doesn't have any.
    @override
    @abstractmethod
    def compute_reward(
        self, achieved_goal: GoalType, desired_goal: GoalType, info: dict[str, t.Any]
    ) -> t.SupportsFloat:
        raise NotImplementedError

    @override
    @abstractmethod
    def compute_terminated(
        self, achieved_goal: GoalType, desired_goal: GoalType, info: dict[str, t.Any]
    ) -> bool:
        raise NotImplementedError

    @override
    @abstractmethod
    def compute_truncated(
        self, achieved_goal: GoalType, desired_goal: GoalType, info: dict[str, t.Any]
    ) -> bool:
        raise NotImplementedError
