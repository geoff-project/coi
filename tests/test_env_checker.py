# SPDX-FileCopyrightText: 2020-2024 CERN
# SPDX-FileCopyrightText: 2023-2024 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

"""Test the check() function."""

from __future__ import annotations

import typing as t

import gymnasium as gym
import matplotlib.pyplot as plt
import numpy as np
from numpy.typing import NDArray
from scipy.optimize import LinearConstraint

from cernml import coi


class MultiGoalParabola(
    coi.SeparableOptGoalEnv[
        NDArray[np.double], NDArray[np.double], NDArray[np.double], NDArray[np.double]
    ],
    coi.Configurable,
):
    # pylint: disable = too-many-ancestors

    action_space = gym.spaces.Box(-1, 1, (2,), dtype=np.double)
    observation_space = gym.spaces.Dict(
        observation=gym.spaces.Box(0.0, np.sqrt(8.0), (1,), dtype=np.double),
        achieved_goal=gym.spaces.Box(-2, 2, (2,), dtype=np.double),
        desired_goal=gym.spaces.Box(-2, 2, (2,), dtype=np.double),
    )
    optimization_space = gym.spaces.Box(-2, 2, (2,), dtype=np.double)
    reward_range = (-np.sqrt(16.0), 0.0)
    objective_range = (0.0, np.sqrt(18.0))
    metadata: dict[str, t.Any] = {
        "render_modes": ["ansi", "human", "matplotlib_figures"],
        "cern.machine": coi.Machine.NO_MACHINE,
        "cern.japc": False,
        "cern.cancellable": False,
    }

    def __init__(self, *, render_mode: str | None = None) -> None:
        self.render_mode = render_mode
        self.pos = self.action_space.sample()
        self.goal = self.action_space.sample()
        self.constraints = [LinearConstraint(np.diag(np.ones(2)), 0.0, 1.0)]

    @property
    def distance(self) -> float:
        return float(np.linalg.norm(self.pos - self.goal))

    def reset(
        self, seed: int | None = None, options: coi.InfoDict | None = None
    ) -> tuple[dict[str, NDArray[np.double]], coi.InfoDict]:
        self.pos = self.action_space.sample()
        self.goal = self.action_space.sample()
        return {
            "observation": np.array([self.distance]),
            "achieved_goal": self.pos.copy(),
            "desired_goal": self.goal.copy(),
        }, {}

    def compute_observation(
        self, action: NDArray[np.double], info: coi.InfoDict
    ) -> coi.GoalObs:
        self.pos += action
        return {
            "observation": np.array([self.distance]),
            "achieved_goal": self.pos.copy(),
            "desired_goal": self.goal.copy(),
        }

    def compute_reward(
        self,
        achieved_goal: NDArray[np.double],
        desired_goal: NDArray[np.double],
        info: coi.InfoDict,
    ) -> float:
        return max(-self.distance, self.reward_range[0])

    def compute_terminated(
        self,
        achieved_goal: NDArray[np.double],
        desired_goal: NDArray[np.double],
        info: coi.InfoDict,
    ) -> bool:
        return bool(np.linalg.norm(achieved_goal - desired_goal, ord=np.inf) < 0.05)

    def compute_truncated(
        self,
        achieved_goal: NDArray[np.double],
        desired_goal: NDArray[np.double],
        info: coi.InfoDict,
    ) -> bool:
        return achieved_goal not in self.observation_space

    def get_initial_params(self) -> NDArray[np.double]:
        obs, _ = self.reset()
        return obs["achieved_goal"]

    def compute_single_objective(self, params: NDArray[np.double]) -> t.SupportsFloat:
        self.pos = params.copy()
        return self.distance

    def render(self, mode: str = "human") -> t.Any:
        if self.render_mode == "human":
            plt.figure()
            xdata, ydata = zip(self.pos, self.goal)
            plt.scatter(xdata, ydata, c=[0, 1])
            return None
        if self.render_mode == "matplotlib_figures":
            xdata, ydata = zip(self.pos, self.goal)
            figure = plt.Figure()
            figure.add_subplot(1, 1, 1).scatter(xdata, ydata, c=[0, 1])
            return [figure]
        if self.render_mode == "ansi":
            return f"{self.pos} -> {self.goal}"
        return super().render()

    def get_config(self) -> coi.Config:
        return coi.Config()

    def apply_config(self, values: coi.ConfigValues) -> None:
        pass


class FunctionParabola(coi.BaseFunctionOptimizable):
    objective_range = (0.0, np.sqrt(18.0))
    metadata: dict[str, t.Any] = {
        "render_modes": ["ansi", "human", "matplotlib_figures"],
        "cern.machine": coi.Machine.NO_MACHINE,
        "cern.japc": False,
        "cern.cancellable": False,
    }

    def __init__(self, *, render_mode: str | None = None) -> None:
        super().__init__(render_mode=render_mode)
        self.pos = np.zeros(2)
        self.time = 0.0
        self.goals: dict[float, NDArray[np.double]] = {}
        self.constraints = [LinearConstraint(np.diag(np.ones(2)), 0.0, 1.0)]

    @property
    def distance(self) -> float:
        return float(np.linalg.norm(self.pos - self.goals[self.time]))

    def get_optimization_space(self, cycle_time: float) -> gym.Space:
        return gym.spaces.Box(-2, 2, (2,))

    def get_initial_params(self, cycle_time: float) -> NDArray[np.double]:
        space = self.get_optimization_space(cycle_time)
        self.time = cycle_time
        self.pos = space.sample()
        self.goals[cycle_time] = space.sample()
        return self.pos.copy()

    def compute_function_objective(
        self, cycle_time: float, params: NDArray[np.double]
    ) -> float:
        self.time = cycle_time
        self.pos = params.copy()
        return self.distance

    def render(self) -> t.Any:
        if self.render_mode == "human":
            plt.figure()
            xdata, ydata = zip(self.pos, self.goals.get(self.time, [0, 0]))
            plt.scatter(xdata, ydata, c=[0, 1])
            return None
        if self.render_mode == "matplotlib_figures":
            xdata, ydata = zip(self.pos, self.goals.get(self.time, [0, 0]))
            figure = plt.Figure()
            figure.add_subplot(1, 1, 1).scatter(xdata, ydata, c=[0, 1])
            return [figure]
        if self.render_mode == "ansi":
            return f"{self.pos} -> {self.time} -> {self.goals.get(self.time)}"
        return super().render()


def test_opt_env() -> None:
    coi.check(MultiGoalParabola())


def test_func_opt() -> None:
    coi.check(FunctionParabola())
