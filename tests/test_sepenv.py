# SPDX-FileCopyrightText: 2020 - 2024 CERN
# SPDX-FileCopyrightText: 2023 - 2024 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

"""Test the SeparableEnv class."""

from unittest.mock import MagicMock

from cernml import coi


def test_step() -> None:
    class Subclass(coi.SeparableEnv):
        reset = MagicMock(name="reset")
        render = MagicMock(name="render")
        compute_observation = MagicMock(name="compute_observation")
        compute_reward = MagicMock(name="compute_reward")
        compute_reward.return_value.__float__.return_value = 545.23
        compute_terminated = MagicMock(name="compute_terminated")
        compute_truncated = MagicMock(name="compute_truncated")

    env = Subclass()
    action = MagicMock(name="action")
    obs, reward, terminated, truncated, info = env.step(action)
    env.compute_observation.assert_called_once_with(action, info)
    assert obs == env.compute_observation.return_value
    env.compute_reward.assert_called_once_with(obs, None, info)
    assert reward == env.compute_reward.return_value
    env.compute_terminated.assert_called_once_with(obs, 545.23, info)
    env.compute_truncated.assert_called_once_with(obs, 545.23, info)
    assert terminated == env.compute_terminated.return_value
    assert truncated == env.compute_truncated.return_value
    assert info == {"reward": 545.23}
