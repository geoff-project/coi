# SPDX-FileCopyrightText: 2020-2024 CERN
# SPDX-FileCopyrightText: 2023-2024 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

# pylint: disable = abstract-method
# pylint: disable = too-few-public-methods

"""An interface that splits calculations into reusable parts."""

import typing as t

import gym
import numpy as np

InfoDict = t.Dict[str, t.Any]
# TODO: Use t.TypedDict with Python 3.8.
GoalObs = t.Dict[str, np.ndarray]


class SeparableEnv(gym.Env):
    """An environment whose calculations nicely separate.

    This interface is superficially similar to `~gym.GoalEnv`, but
    doesn't pose any requirements to the observation space. (By
    contrast, `~gym.GoalEnv` requires that the observation space is a
    dict with keys ``"observation"``, ``"desired_goal"`` and
    ``"achieved_goal"``.) The only requirement is that the calculation
    of observation, reward and end-of-episode can be separated into
    distinct steps.

    This makes two things possible:

    - replacing `compute_observation()` with a function approximator,
      e.g. a neural network;
    - estimating the goodness of the very initial observation of an
      episode via ``env.compute_reward(env.reset(), None, {})``.

    Because of these use cases, all state transition should be
    restricted to `compute_observation()`. In particular, it must be
    possible to call `compute_reward()` and `compute_done()` multiple
    times without changing the internal state of the environment.
    """

    def step(self, action: np.ndarray) -> t.Tuple[np.ndarray, float, bool, InfoDict]:
        """Implementation of `gym.Env.step()`.

        This calls in turn the three new abstract methods:
        `compute_observation()`, `compute_reward()`, and
        `compute_done()`.
        """
        info: InfoDict = {}
        obs = self.compute_observation(action, info)
        reward = self.compute_reward(obs, None, info)
        done = self.compute_done(obs, reward, info)
        return obs, reward, done, info

    def compute_observation(self, action: np.ndarray, info: InfoDict) -> np.ndarray:
        """Compute the next observation if *action* is taken.

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
        raise NotImplementedError()

    def compute_reward(self, obs: np.ndarray, goal: None, info: InfoDict) -> float:
        """Compute the next observation if *action* is taken.

        This externalizes the reward function. In this regard, it is
        similar to `gym.GoalEnv.compute_reward()`, but it doesn't impose
        any structure on the observation space.

        Note that this function should be free of side-effects or
        modifications of *self*. In particular, the user is allowed to
        do multiple calls to ``env.compute_reward(obs, None, {})`` and
        always expect the same result.

        Args:
            obs: The observation calculated by `~gym.Env.reset()` or
                `compute_observation()`.
            goal: A dummy parameter to stay compatible with the
                `~gym.GoalEnv` API. This parameter generally is None. If
                you want a multi-goal environment, consider
                `SeparableGoalEnv`.
            info: an info dictionary with additional information.
                It may or may not have been passed to
                `compute_observation()` before.

        Returns:
            float: the reward that corresponds to the given observation.
                This value is returned by `step()`.
        """
        raise NotImplementedError()

    def compute_done(self, obs: np.ndarray, reward: float, info: InfoDict) -> bool:
        """Compute whether the episode ends in this step.

        This externalizes the determination of the end of episode. This
        function should be free of side-effects or modifications of
        *self*. In particular, it must be possible to call
        ``env.compute_done(obs, reward, {})`` multiple times and always
        get the same result.

        If you want to indicate that the episode has ended in a success,
        consider setting ``info["success"] = True``.

        Args:
            obs: The observation calculated by `~gym.Env.reset()` or
                `compute_observation()`.
            reward: The observation calculated by `compute_reward()`.
            info: an info dictionary with additional information. It may
                or may not have been passed to `compute_reward()`
                before.

        Returns:
            bool: True if the episode has ended, False otherwise.
        """
        raise NotImplementedError()


class SeparableGoalEnv(gym.GoalEnv):
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
