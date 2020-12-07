#!/usr/bin/env python
"""Test the check_env() function."""

# pylint: disable = missing-class-docstring, missing-function-docstring

import typing as t

import gym
import numpy as np
from matplotlib import pyplot

from cernml.coi import Machine, SeparableOptGoalEnv, check_env


class MultiGoalParabola(SeparableOptGoalEnv):
    action_space = gym.spaces.Box(-1, 1, (2,))
    observation_space = gym.spaces.Dict(
        observation=gym.spaces.Box(0.0, np.sqrt(8.0), (1,)),
        achieved_goal=gym.spaces.Box(-2, 2, (2,)),
        desired_goal=gym.spaces.Box(-2, 2, (2,)),
    )
    optimization_space = gym.spaces.Box(-2, 2, (2,))
    reward_range = (-np.sqrt(8.0), 0.0)
    objective_range = (0.0, np.sqrt(8.0))
    metadata = {
        "render.modes": ["ansi", "human", "qtembed"],
        "cern.machine": Machine.NoMachine,
    }

    def __init__(self) -> None:
        self.pos = self.action_space.sample()
        self.goal = self.action_space.sample()

    @property
    def distance(self) -> float:
        return np.linalg.norm(self.pos - self.goal)

    def reset(self) -> np.ndarray:
        self.pos = self.action_space.sample()
        self.goal = self.action_space.sample()
        return dict(
            observation=np.array([self.distance]),
            achieved_goal=self.pos.copy(),
            desired_goal=self.goal.copy(),
        )

    def compute_observation(
        self, action: np.ndarray, info: t.Dict
    ) -> t.Dict[str, np.ndarray]:
        self.pos += action
        return dict(
            observation=np.array([self.distance]),
            achieved_goal=self.pos.copy(),
            desired_goal=self.goal.copy(),
        )

    def compute_reward(
        self,
        achieved_goal: np.ndarray,
        desired_goal: np.ndarray,
        info: t.Dict[str, t.Any],
    ) -> float:
        return max(-self.distance, self.reward_range[0])

    def compute_done(
        self,
        obs: t.Dict[str, np.ndarray],
        reward: float,
        info: t.Dict[str, t.Any],
    ) -> bool:
        success = obs["observation"] < 0.05
        done = success or obs not in self.observation_space
        if done:
            info["success"] = success
        return done

    def get_initial_params(self) -> np.ndarray:
        return self.reset()["achieved_goal"]

    def compute_single_objective(self, params: np.ndarray) -> float:
        self.pos = params.copy()
        return self.distance

    def render(self, mode: str = "human", **kwargs: t.Any) -> t.Any:
        if mode in ("human", "qtembed"):
            xdata, ydata = zip(self.pos, self.goal)
            pyplot.scatter(xdata, ydata, c=[0, 1])
            return None
        if mode == "ansi":
            return f"{self.pos} -> {self.goal}"
        return super().render(mode, **kwargs)

    def seed(self, seed: t.Optional[int] = None) -> t.List[int]:
        return [
            *self.action_space.seed(seed),
            *self.observation_space.seed(seed),
        ]


def test_check_env() -> None:
    check_env(MultiGoalParabola())
