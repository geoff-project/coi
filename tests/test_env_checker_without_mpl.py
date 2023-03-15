"""Test the check() function if matplotlib is not importable."""

# pylint: disable = import-outside-toplevel
# pylint: disable = missing-class-docstring
# pylint: disable = missing-function-docstring
# pylint: disable = redefined-outer-name

import sys
import typing as t

import gym
import numpy as np
import pytest


@pytest.fixture
def no_matplotlib() -> t.Iterator[None]:
    backup = sys.modules.copy()
    try:
        # Force reload of cernml packages.
        for name in backup:
            if name.startswith("cernml"):
                del sys.modules[name]
        # Forbid (re-)import of matplotlib packages.
        for name in backup:
            if name.startswith("matplotlib"):
                sys.modules[name] = None  # type: ignore
        yield
    finally:
        # Never assign to `sys.modules`, manipulate the object that is
        # already there.
        sys.modules.update(backup)


def test_sep_env(no_matplotlib: None) -> None:
    from cernml import coi

    class SeparableParabola(coi.SeparableEnv):
        action_space = gym.spaces.Box(-1, 1, (2,))
        observation_space = gym.spaces.Box(-2, 2, (2,))
        reward_range = (-np.sqrt(16.0), 0.0)
        metadata = {
            "render.modes": ["ansi"],
            "cern.machine": coi.Machine.NO_MACHINE,
            "cern.japc": False,
            "cern.cancellable": False,
        }

        def __init__(self) -> None:
            self.pos = self.action_space.sample()
            self.goal = self.action_space.sample()

        @property
        def distance(self) -> float:
            return float(np.linalg.norm(self.pos - self.goal))

        def reset(self) -> np.ndarray:
            self.pos = self.action_space.sample()
            self.goal = self.action_space.sample()
            return self.pos - self.goal

        def compute_observation(self, action: np.ndarray, info: t.Dict) -> np.ndarray:
            self.pos += action
            return np.clip(
                self.pos - self.goal,
                self.observation_space.low,
                self.observation_space.high,
            )

        def compute_reward(
            self, obs: np.ndarray, goal: None, info: t.Dict[str, t.Any]
        ) -> float:
            return max(-np.linalg.norm(obs), self.reward_range[0])

        def compute_done(
            self, obs: np.ndarray, reward: float, info: t.Dict[str, t.Any]
        ) -> bool:
            success = self.distance < 0.05
            return success or obs not in self.observation_space

        def render(self, mode: str = "human") -> t.Any:
            if mode == "ansi":
                return f"{self.pos} -> {self.goal}"
            return super().render(mode)

    assert no_matplotlib is None
    coi.check(SeparableParabola(), warn=False)
