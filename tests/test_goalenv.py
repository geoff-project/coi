# SPDX-FileCopyrightText: 2020-2024 CERN
# SPDX-FileCopyrightText: 2023-2024 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

"""Test our implementation of `GoalEnv`."""

from unittest.mock import Mock

import gymnasium as gym
import pytest

from cernml import coi


def test_require_dict() -> None:
    class Subclass(coi.GoalEnv):
        observation_space = gym.spaces.Box(-1, 1)  # type: ignore[assignment]

    with pytest.raises(gym.error.Error, match="requires .* of type gym.spaces.Dict$"):
        Subclass().reset()  # type: ignore[abstract]


REQUIRED_KEYS = ("observation", "achieved_goal", "desired_goal")


@pytest.mark.parametrize("missing_key", REQUIRED_KEYS)
def test_requires_keys(missing_key: str) -> None:
    keys = set(REQUIRED_KEYS)
    keys.remove(missing_key)

    class Subclass(coi.GoalEnv):
        observation_space = gym.spaces.Dict(dict.fromkeys(keys, gym.spaces.Box(-1, 1)))

    with pytest.raises(gym.error.Error, match=f'requires the "{missing_key}" key'):
        Subclass().reset()  # type: ignore[abstract]


def test_works(monkeypatch: pytest.MonkeyPatch) -> None:
    reset = Mock()
    seed = Mock()
    monkeypatch.setattr(gym.Env, "reset", reset)
    spaces: dict[str, gym.spaces.Space] = dict.fromkeys(
        REQUIRED_KEYS, gym.spaces.Box(-1, 1)
    )

    class Subclass(coi.GoalEnv):
        observation_space = gym.spaces.Dict(spaces)

    res = Subclass().reset(seed=seed)  # type: ignore[abstract]
    assert res == reset.return_value
    reset.assert_called_once_with(seed=seed)
