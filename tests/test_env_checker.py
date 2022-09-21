"""Test the check() function."""

# pylint: disable = missing-class-docstring
# pylint: disable = missing-function-docstring

import typing as t

import gym
import matplotlib.figure
import numpy as np
from matplotlib import pyplot
from scipy.optimize import LinearConstraint

from cernml import coi


class MultiGoalParabola(coi.SeparableOptGoalEnv, coi.Configurable):

    # pylint: disable = too-many-ancestors

    action_space = gym.spaces.Box(-1, 1, (2,))
    observation_space = gym.spaces.Dict(
        observation=gym.spaces.Box(0.0, np.sqrt(8.0), (1,)),
        achieved_goal=gym.spaces.Box(-2, 2, (2,)),
        desired_goal=gym.spaces.Box(-2, 2, (2,)),
    )
    optimization_space = gym.spaces.Box(-2, 2, (2,))
    reward_range = (-np.sqrt(16.0), 0.0)
    objective_range = (0.0, np.sqrt(18.0))
    metadata = {
        "render.modes": ["ansi", "human", "matplotlib_figures"],
        "cern.machine": coi.Machine.NO_MACHINE,
        "cern.japc": False,
        "cern.cancellable": False,
    }

    def __init__(self) -> None:
        self.pos = self.action_space.sample()
        self.goal = self.action_space.sample()
        self.constraints = [LinearConstraint(np.diag(np.ones(2)), 0.0, 1.0)]

    @property
    def distance(self) -> float:
        return np.linalg.norm(self.pos - self.goal)

    def reset(self) -> t.Dict[str, np.ndarray]:
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
        success = all(obs["observation"] < 0.05)
        done = success or obs not in self.observation_space
        if done:
            info["success"] = success
        return done

    def get_initial_params(self) -> np.ndarray:
        return self.reset()["achieved_goal"]

    def compute_single_objective(self, params: np.ndarray) -> float:
        self.pos = params.copy()
        return self.distance

    def render(self, mode: str = "human") -> t.Any:
        if mode == "human":
            pyplot.figure()
            xdata, ydata = zip(self.pos, self.goal)
            pyplot.scatter(xdata, ydata, c=[0, 1])
            return None
        if mode == "matplotlib_figures":
            xdata, ydata = zip(self.pos, self.goal)
            figure = matplotlib.figure.Figure()
            figure.add_subplot(1, 1, 1).scatter(xdata, ydata, c=[0, 1])
            return [figure]
        if mode == "ansi":
            return f"{self.pos} -> {self.goal}"
        return super().render(mode)

    def seed(self, seed: t.Optional[int] = None) -> t.List[int]:
        return [
            *self.action_space.seed(seed),
            *self.observation_space.seed(seed),
        ]

    def get_config(self) -> coi.Config:
        return coi.Config()

    def apply_config(self, values: coi.ConfigValues) -> None:
        pass


class FunctionParabola(coi.FunctionOptimizable):
    objective_range = (0.0, np.sqrt(18.0))
    metadata = {
        "render.modes": ["ansi", "human", "matplotlib_figures"],
        "cern.machine": coi.Machine.NO_MACHINE,
        "cern.japc": False,
        "cern.cancellable": False,
    }

    def __init__(self) -> None:
        self.pos = np.zeros(2)
        self.time = 0.0
        self.goals: t.Dict[float, np.ndarray] = {}
        self.constraints = [LinearConstraint(np.diag(np.ones(2)), 0.0, 1.0)]

    @property
    def distance(self) -> float:
        return np.linalg.norm(self.pos - self.goals[self.time])

    def get_optimization_space(self, cycle_time: float) -> gym.Space:
        return gym.spaces.Box(-2, 2, (2,))

    def get_initial_params(self, cycle_time: float) -> np.ndarray:
        space = self.get_optimization_space(cycle_time)
        self.time = cycle_time
        self.pos = space.sample()
        self.goals[cycle_time] = space.sample()
        return self.pos.copy()

    def compute_function_objective(
        self, cycle_time: float, params: np.ndarray
    ) -> float:
        self.time = cycle_time
        self.pos = params.copy()
        return self.distance

    def render(self, mode: str = "human") -> t.Any:
        if mode == "human":
            pyplot.figure()
            xdata, ydata = zip(self.pos, self.goals.get(self.time, [0, 0]))
            pyplot.scatter(xdata, ydata, c=[0, 1])
            return None
        if mode == "matplotlib_figures":
            xdata, ydata = zip(self.pos, self.goals.get(self.time, [0, 0]))
            figure = matplotlib.figure.Figure()
            figure.add_subplot(1, 1, 1).scatter(xdata, ydata, c=[0, 1])
            return [figure]
        if mode == "ansi":
            return f"{self.pos} -> {self.time} -> {self.goals.get(self.time)}"
        return super().render(mode)


def test_opt_env() -> None:
    coi.check(MultiGoalParabola())


def test_func_opt() -> None:
    coi.check(FunctionParabola())
