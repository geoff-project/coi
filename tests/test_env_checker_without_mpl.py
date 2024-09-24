# SPDX-FileCopyrightText: 2020 - 2024 CERN
# SPDX-FileCopyrightText: 2023 - 2024 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

"""Test the check() function if matplotlib is not importable."""

from __future__ import annotations

import sys
import typing as t

import gymnasium as gym
import numpy as np
import pytest
from numpy.typing import NDArray


@pytest.fixture
def no_matplotlib() -> t.Iterator[None]:  # noqa: PT004
    backup = sys.modules.copy()
    try:
        # Force reload of cernml packages.
        for name in backup:
            if name.startswith("cernml"):
                del sys.modules[name]
        # Forbid (re-)import of matplotlib packages.
        for name in backup:
            if name.startswith("matplotlib"):
                sys.modules[name] = None  # type: ignore[assignment]
        yield
    finally:
        # Never assign to `sys.modules`, manipulate the object that is
        # already there.
        sys.modules.update(backup)


def test_sep_env(no_matplotlib: None) -> None:
    from cernml import coi

    class SeparableParabola(coi.SeparableEnv[NDArray[np.double], NDArray[np.double]]):
        action_space = gym.spaces.Box(-1, 1, (2,))
        observation_space = gym.spaces.Box(-2, 2, (2,))
        metadata: dict[str, t.Any] = {
            "render_modes": ["ansi"],
            "cern.machine": coi.Machine.NO_MACHINE,
            "cern.japc": False,
            "cern.cancellable": False,
        }

        def __init__(self, *, render_mode: str | None = None) -> None:
            self.render_mode = render_mode
            self.pos = self.action_space.sample()
            self.goal = self.action_space.sample()

        @property
        def distance(self) -> float:
            return float(np.linalg.norm(self.pos - self.goal))

        def reset(
            self, seed: int | None = None, options: coi.InfoDict | None = None
        ) -> tuple[NDArray[np.double], coi.InfoDict]:
            super().reset(seed=seed)
            self.pos = self.action_space.sample()
            self.goal = self.action_space.sample()
            return self.pos - self.goal, {}

        def compute_observation(
            self, action: NDArray[np.double], info: coi.InfoDict
        ) -> NDArray[np.double]:
            self.pos += action
            return np.clip(
                self.pos - self.goal,
                self.observation_space.low,
                self.observation_space.high,
            )

        def compute_reward(
            self, obs: NDArray[np.double], goal: None, info: coi.InfoDict
        ) -> float:
            return float(-np.linalg.norm(obs))

        def compute_terminated(
            self,
            obs: NDArray[np.double],
            reward: float,
            info: coi.InfoDict,
        ) -> bool:
            return reward < 0.05

        def compute_truncated(
            self,
            obs: NDArray[np.double],
            reward: float,
            info: coi.InfoDict,
        ) -> bool:
            return obs not in self.observation_space

        def render(self) -> t.Any:
            if self.render_mode == "ansi":
                return f"{self.pos} -> {self.goal}"
            return super().render()

    assert no_matplotlib is None
    coi.check(SeparableParabola(), warn=False)
