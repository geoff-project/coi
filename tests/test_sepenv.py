# SPDX-FileCopyrightText: 2020-2024 CERN
# SPDX-FileCopyrightText: 2023-2024 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

"""Test the SeparableEnv class."""

from unittest.mock import Mock

from cernml import coi


def test_step() -> None:
    class Subclass(coi.SeparableEnv):
        reset = Mock(name="reset")
        render = Mock(name="render")
        compute_observation = Mock(name="compute_observation")
        compute_reward = Mock(name="compute_reward")
        compute_terminated = Mock(name="compute_terminated")
        compute_truncated = Mock(name="compute_truncated")

    env = Subclass()
    action = Mock(name="action")
    obs, reward, terminated, truncated, info = env.step(action)
    env.compute_observation.assert_called_once_with(action, info)
    assert obs == env.compute_observation.return_value
    env.compute_reward.assert_called_once_with(obs, None, info)
    assert reward == env.compute_reward.return_value
    env.compute_terminated.assert_called_once_with(obs, None, info)
    env.compute_truncated.assert_called_once_with(obs, None, info)
    assert terminated == env.compute_terminated.return_value
    assert truncated == env.compute_truncated.return_value
    assert info == {"reward": env.compute_reward.return_value}
