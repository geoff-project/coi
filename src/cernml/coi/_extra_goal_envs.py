# SPDX-FileCopyrightText: 2020-2024 CERN
# SPDX-FileCopyrightText: 2023-2024 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

"""Interfaces that combine two or more base interfaces."""

import typing as t
from abc import ABCMeta

import numpy as np

from ._goalenv import GoalEnv
from ._single_opt import SingleOptimizable

InfoDict = t.Dict[str, t.Any]
# TODO: Use t.TypedDict with Python 3.8.
GoalObs = t.Dict[str, np.ndarray]


class SeparableGoalEnv(GoalEnv):
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

    def step(self, action: np.ndarray) -> t.Tuple[GoalObs, float, bool, InfoDict]:
        """Implementation of `gym.Env.step()`.

        This calls in turn the three new abstract methods:
        `compute_observation()`, `~gym.GoalEnv.compute_reward()`, and
        `compute_done()`.
        """
        info: InfoDict = {}
        obs = self.compute_observation(action, info)
        reward = self.compute_reward(
            obs["achieved_goal"],
            obs["desired_goal"],
            info,
        )
        done = self.compute_done(obs, reward, info)
        return obs, reward, done, info

    def compute_observation(self, action: np.ndarray, info: InfoDict) -> GoalObs:
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
        raise NotImplementedError()

    def compute_done(self, obs: GoalObs, reward: float, info: InfoDict) -> bool:
        """Compute whether the episode ends in this step.

        This externalizes the determination of the end of episode. This
        function should be free of side-effects or modifications of
        *self*. In particular, it must be possible to call
        ``env.compute_done(obs, reward, {})`` multiple times and always
        expect the same result.

        If you want to indicate that the episode has ended in a success,
        consider setting ``info["success"] = True``.

        Args:
            obs: The observation calculated by `~gym.Env.reset()` or
                `compute_observation()`.
            reward: The observation calculated by
                `~gym.GoalEnv.compute_reward()`.
            info: an info dictionary with additional information. It may
                or may not have been passed to
                `~gym.GoalEnv.compute_reward()` before.

        Returns:
            True if the episode has ended, False otherwise.
        """
        raise NotImplementedError()


class OptGoalEnv(GoalEnv, SingleOptimizable, metaclass=ABCMeta):
    """An optimizable multi-goal environment.

    This is an intersection of `~gym.GoalEnv` and `SingleOptimizable`.
    Any class that inherits from both, also inherits from this class.
    """

    @classmethod
    def __subclasshook__(cls, other: type) -> t.Any:
        if cls is OptGoalEnv:
            bases = other.__mro__
            return GoalEnv in bases and SingleOptimizable in bases
        return NotImplemented


class SeparableOptGoalEnv(SeparableGoalEnv, SingleOptimizable, metaclass=ABCMeta):
    """An optimizable and separable multi-goal environment.

    This is an intersection of `SeparableGoalEnv` and
    `SingleOptimizable`. Any class that inherits from both, also
    inherits from this class.
    """

    @classmethod
    def __subclasshook__(cls, other: type) -> t.Any:
        if cls is SeparableOptGoalEnv:
            bases = other.__mro__
            return SeparableGoalEnv in bases and SingleOptimizable in bases
        return NotImplemented
