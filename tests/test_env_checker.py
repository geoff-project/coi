# SPDX-FileCopyrightText: 2020-2024 CERN
# SPDX-FileCopyrightText: 2023-2024 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

"""Test the check() function."""

from __future__ import annotations

import functools
import typing as t
from collections import Counter
from unittest.mock import Mock

import gymnasium as gym
import matplotlib.pyplot as plt
import numpy as np
import pytest
from numpy.typing import NDArray
from scipy.optimize import LinearConstraint

from cernml import coi


class MockFigureMeta(type):
    """Mock metaclass to override instance checks.

    This exists in order to pass an `assert isinstance(..., Figure)`
    check in `assert_matplotlib_figures()`.
    """

    figure_class: Mock

    def __instancecheck__(cls, instance: object) -> bool:
        return instance == cls.figure_class.return_value


@pytest.fixture(autouse=True)
def pyplot(monkeypatch: pytest.MonkeyPatch) -> Mock:
    mock = Mock(name="matplotlib.pyplot")
    # Ensure that `plt.Figure()` return value doesn't have a `number`
    # attribute (unlike the return value of `plt.figure()`). Otherwise,
    # it won't pass for an unmanaged figure.
    mock.Figure.return_value.mock_add_spec(plt.Figure, spec_set=True)

    class MockFigure(metaclass=MockFigureMeta):
        figure_class = mock.Figure

    monkeypatch.setattr("cernml.coi.checkers._render.Figure", MockFigure)
    monkeypatch.setitem(globals(), "plt", mock)
    return mock


class CallStatsMixin:
    """Mixin that counts all method calls.

    Attributes:
        call_count: A dict mapping method name to number of times this
            method has been called.
    """

    def __init__(self) -> None:
        super().__init__()
        self.call_count = Counter[str]()

    def __getattribute__(self, name: str) -> object:
        attr = super().__getattribute__(name)
        if name.startswith("_") or not callable(attr):
            return attr

        @functools.wraps(attr)
        def wrapper(*args: object, **kwargs: object) -> object:
            self.call_count[name] += 1
            return attr(*args, **kwargs)

        return wrapper


class MultiGoalParabola(
    coi.SeparableOptGoalEnv[
        NDArray[np.double], NDArray[np.double], NDArray[np.double], NDArray[np.double]
    ],
    coi.Configurable,
    CallStatsMixin,
):
    # pylint: disable = too-many-ancestors

    action_space = gym.spaces.Box(-1, 1, (2,), dtype=np.double)
    observation_space = gym.spaces.Dict(
        observation=gym.spaces.Box(0.0, np.sqrt(3**2 + 3**2), (1,), dtype=np.double),
        achieved_goal=gym.spaces.Box(-2, 2, (2,), dtype=np.double),
        desired_goal=gym.spaces.Box(-2, 2, (2,), dtype=np.double),
    )
    optimization_space = gym.spaces.Box(-2, 2, (2,), dtype=np.double)
    reward_range = (-np.sqrt(16.0), 0.0)
    objective_range = (0.0, np.sqrt(3**2 + 3**2))
    metadata: dict[str, t.Any] = {
        "render_modes": ["ansi", "human", "matplotlib_figures"],
        "cern.machine": coi.Machine.NO_MACHINE,
        "cern.japc": False,
        "cern.cancellable": False,
    }

    def __init__(self, *, render_mode: str | None = None) -> None:
        # Don't use super(), `typing.Protocol` breaks MRO.
        coi.SeparableOptGoalEnv.__init__(self)
        coi.Configurable.__init__(self)
        CallStatsMixin.__init__(self)
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
        if self.render_mode == "human":
            self.render()
        return {
            "observation": np.array([self.distance]),
            "achieved_goal": self.pos.copy(),
            "desired_goal": self.goal.copy(),
        }, {}

    def compute_observation(
        self, action: NDArray[np.double], info: coi.InfoDict
    ) -> coi.GoalObs:
        assert action in self.action_space
        self.pos += action
        if self.render_mode == "human":
            self.render()
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
        assert params in self.optimization_space
        self.pos = params.copy()
        if self.render_mode == "human":
            self.render()
        return self.distance

    def render(self) -> t.Any:
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


class FunctionParabola(coi.FunctionOptimizable, CallStatsMixin):
    optimization_space = gym.spaces.Box(-2, 2, (2,))
    objective_range = (0.0, np.sqrt(4**2 + 4**2))
    metadata: dict[str, t.Any] = {
        "render_modes": ["ansi", "human", "matplotlib_figures"],
        "cern.machine": coi.Machine.NO_MACHINE,
        "cern.japc": False,
        "cern.cancellable": False,
    }

    def __init__(self, *, render_mode: str | None = None) -> None:
        # Don't use super(), `typing.Protocol` breaks MRO.
        coi.FunctionOptimizable.__init__(self, render_mode=render_mode)
        CallStatsMixin.__init__(self)
        self.pos = np.zeros(2)
        self.time = 0.0
        self.goals: dict[float, NDArray[np.double]] = {}
        self.constraints = [LinearConstraint(np.diag(np.ones(2)), 0.0, 1.0)]

    @property
    def distance(self) -> float:
        return float(np.linalg.norm(self.pos - self.goals[self.time]))

    def get_optimization_space(self, cycle_time: float) -> gym.Space:
        return self.optimization_space

    def get_initial_params(self, cycle_time: float) -> NDArray[np.double]:
        space = self.get_optimization_space(cycle_time)
        self.time = cycle_time
        self.pos = space.sample()
        self.goals[cycle_time] = space.sample()
        return self.pos.copy()

    def compute_function_objective(
        self, cycle_time: float, params: NDArray[np.double]
    ) -> float:
        assert params in self.get_optimization_space(cycle_time)
        self.time = cycle_time
        self.pos = params.copy()
        if self.render_mode == "human":
            self.render()
        return self.distance

    def override_skeleton_points(self) -> list[float]:
        return [500.0, 600.0, 700.0]

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


@pytest.mark.parametrize("render_mode", [None, "human", "ansi", "matplotlib_figures"])
def test_opt_env(pyplot: Mock, render_mode: str | None) -> None:
    env = MultiGoalParabola(render_mode=render_mode)
    coi.check(env, headless=False)
    assert env.call_count["reset"] > 10
    assert env.call_count["step"] > 10
    assert env.call_count["get_initial_params"] == 1
    assert env.call_count["compute_single_objective"] == 1
    assert env.call_count["get_config"] == 1
    assert env.call_count["apply_config"] == 1
    if render_mode:
        assert env.call_count["render"] > 0
    else:
        assert env.call_count["render"] == 0
    if render_mode == "human":
        pyplot.figure.assert_called()
        pyplot.scatter.assert_called()
    elif render_mode == "matplotlib_figures":
        pyplot.Figure.assert_called_with()
        figure = pyplot.Figure.return_value
        figure.add_subplot.assert_called_with(1, 1, 1)
        axes = figure.add_subplot.return_value
        axes.scatter.assert_called()


@pytest.mark.parametrize("render_mode", [None, "human", "ansi", "matplotlib_figures"])
def test_func_opt(pyplot: Mock, render_mode: str | None) -> None:
    env = FunctionParabola(render_mode=render_mode)
    coi.check(env, headless=False)
    assert env.call_count["get_optimization_space"] > 0
    assert env.call_count["override_skeleton_points"] > 0
    assert env.call_count["get_initial_params"] == 3
    assert env.call_count["compute_function_objective"] == 3
    if render_mode:
        assert env.call_count["render"] > 0
    else:
        assert env.call_count["render"] == 0
    if render_mode == "human":
        pyplot.figure.assert_called()
        pyplot.scatter.assert_called()
    elif render_mode == "matplotlib_figures":
        pyplot.Figure.assert_called_with()
        figure = pyplot.Figure.return_value
        figure.add_subplot.assert_called_with(1, 1, 1)
        axes = figure.add_subplot.return_value
        axes.scatter.assert_called()
