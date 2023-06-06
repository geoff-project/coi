# SPDX-FileCopyrightText: 2020-2023 CERN
# SPDX-FileCopyrightText: 2023 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

# pylint: disable = missing-class-docstring
# pylint: disable = missing-function-docstring
# pylint: disable = redefined-outer-name

"""Test the SeparableEnv class."""

from unittest.mock import Mock

from cernml import coi


def test_step() -> None:
    class Subclass(coi.SeparableEnv):
        reset = Mock()
        render = Mock()
        compute_observation = Mock()
        compute_reward = Mock()
        compute_done = Mock()

    env = Subclass()
    action = Mock()
    obs, reward, done, info = env.step(action)
    env.compute_observation.assert_called_once_with(action, info)
    assert obs == env.compute_observation.return_value
    env.compute_reward.assert_called_once_with(obs, None, info)
    assert reward == env.compute_reward.return_value
    env.compute_done.assert_called_once_with(obs, reward, info)
    assert done == env.compute_done.return_value
    assert info == {}  # pylint: disable=use-implicit-booleaness-not-comparison
