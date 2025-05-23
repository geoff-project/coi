# SPDX-FileCopyrightText: 2020 - 2025 CERN
# SPDX-FileCopyrightText: 2022 - 2025 Farama Foundation
# SPDX-FileCopyrightText: 2023 - 2025 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+
# SPDX-License-Identifier: MIT AND (GPL-3.0-or-later OR EUPL-1.2+)

"""This package vendors the `.GoalEnv` class of Gymnasium Robotics.

If :doc:`Gymnasium-Robotics <gymrob:content/multi-goal_api>` is
installed, its `gymnasium_robotics.core.GoalEnv` class is used. if it
isn't, this package provides its own, compatible implementation.
"""

from abc import abstractmethod
from contextlib import suppress
from typing import Any, Generic, Optional, SupportsFloat, TypeVar

import gymnasium as gym
from gymnasium import error
from gymnasium.core import ActType, ObsType
from typing_extensions import TypedDict

__all__ = (
    "GoalEnv",
    "GoalObs",
    "GoalType",
)

GoalType = TypeVar("GoalType")  # pylint: disable = invalid-name


class GoalObs(TypedDict, Generic[ObsType, GoalType]):
    """Type annotation for the observation type of `GoalEnv`."""

    observation: ObsType
    """The actual observation of the environment."""

    desired_goal: GoalType
    """The goal that the agent has to achieved."""

    achieved_goal: GoalType
    """The goal that the agent has currently achieved instead. The
    objective of the environments is for this value to be close to
    *desired_goal*."""


class GoalEnv(gym.Env[Any, ActType], Generic[ObsType, GoalType, ActType]):
    r"""A goal-based environment.

    It functions just as any regular Gymnasium environment but it
    imposes a required structure on the observation_space. More
    concretely, the observation space is required to contain at least
    three elements, namely `observation`, `desired_goal`, and
    `achieved_goal`. Here, `desired_goal` specifies the goal that the
    agent should attempt to achieve. `achieved_goal` is the goal that it
    currently achieved instead. `observation` contains the actual
    observations of the environment as per usual.

    - :meth:`compute_reward` - Externalizes the reward function by
      taking the achieved and desired goal, as well as extra
      information. Returns reward.
    - :meth:`compute_terminated` - Returns boolean termination depending
      on the achieved and desired goal, as well as extra information.
    - :meth:`compute_truncated` - Returns boolean truncation depending
      on the achieved and desired goal, as well as extra information.
    """

    observation_space: gym.spaces.Dict  # type: ignore[assignment]

    @abstractmethod
    def reset(
        self, *, seed: Optional[int] = None, options: Optional[dict[str, Any]] = None
    ) -> tuple[GoalObs, dict[str, Any]]:
        """Reset the environment.

        In addition, check if the observation space is correct by
        inspecting the `observation`, `achieved_goal`, and
        `desired_goal` keys.
        """
        super().reset(seed=seed)
        # Enforce that each GoalEnv uses a Goal-compatible observation
        # space.
        ob_space = self.observation_space
        if not isinstance(ob_space, gym.spaces.Dict):
            raise error.Error(
                "GoalEnv requires an observation space of type gym.spaces.Dict"
            )
        for key in ["observation", "achieved_goal", "desired_goal"]:
            if key not in ob_space.spaces:
                raise error.Error(
                    f'GoalEnv requires the "{key}" key to be part of the '
                    f"observation dictionary."
                )
        return None  # type: ignore[return-value]

    @abstractmethod
    def compute_reward(
        self, achieved_goal: GoalType, desired_goal: GoalType, info: dict[str, Any]
    ) -> SupportsFloat:
        """Compute the step reward.

        This externalizes the reward function and makes it dependent on
        a desired goal and the one that was achieved.

        If you wish to include additional rewards that are independent
        of the goal, you can include the necessary values
        to derive it in 'info' and compute it accordingly.

        Args:
            achieved_goal (object): the goal that was achieved during
                execution
            desired_goal (object): the desired goal that we asked the
                agent to attempt to achieve
            info (dict): an info dictionary with additional information

        Returns:
            float: The reward that corresponds to the provided achieved
                goal w.r.t. to the desired goal. Note that the following
                should always hold true:

                    ob, reward, terminated, truncated, info = env.step()
                    assert reward == env.compute_reward(
                        ob['achieved_goal'], ob['desired_goal'], info
                    )
        """
        raise NotImplementedError

    @abstractmethod
    def compute_terminated(
        self, achieved_goal: GoalType, desired_goal: GoalType, info: dict[str, Any]
    ) -> bool:
        """Compute the step termination.

        Allows to customize the termination states depending on the
        desired and the achieved goal.

        If you wish to determine termination states independent of the
        goal, you can include necessary values to derive it in 'info'
        and compute it accordingly. The envirtonment reaches
        a termination state when this state leads to an episode ending
        in an episodic task thus breaking .

        More information can be found in: https://farama.org/New-Step-API#theory

        Termination states are

        Args:
            achieved_goal (object): the goal that was achieved during
                execution
            desired_goal (object): the desired goal that we asked the
                agent to attempt to achieve
            info (dict): an info dictionary with additional information

        Returns:
            bool: The termination state that corresponds to the provided
                achieved goal w.r.t. to the desired goal. Note that the
                following should always hold true:

                    ob, reward, terminated, truncated, info = env.step()
                    assert terminated == env.compute_terminated(
                        ob['achieved_goal'], ob['desired_goal'], info
                    )
        """
        raise NotImplementedError

    @abstractmethod
    def compute_truncated(
        self, achieved_goal: GoalType, desired_goal: GoalType, info: dict[str, Any]
    ) -> bool:
        """Compute the step truncation.

        Allows to customize the truncated states depending on the
        desired and the achieved goal.

        If you wish to determine truncated states independent of the
        goal, you can include necessary values to derive it in 'info'
        and compute it accordingly. Truncated states are those that are
        out of the scope of the Markov Decision Process (MDP) such as
        time constraints in a continuing task.

        More information can be found in: https://farama.org/New-Step-API#theory

        Args:
            achieved_goal (object): the goal that was achieved during
                execution
            desired_goal (object): the desired goal that we asked the
                agent to attempt to achieve
            info (dict): an info dictionary with additional information

        Returns:
            bool: The truncated state that corresponds to the provided
                achieved goal w.r.t. to the desired goal. Note that the
                following should always hold true:

                    ob, reward, terminated, truncated, info = env.step()
                    assert truncated == env.compute_truncated(
                        ob['achieved_goal'], ob['desired_goal'], info
                    )
        """
        raise NotImplementedError


with suppress(ImportError):
    from gymnasium_robotics import (  # type: ignore[no-redef, import-not-found]
        GoalEnv,
    )
