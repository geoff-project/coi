# SPDX-FileCopyrightText: 2020 - 2025 CERN
# SPDX-FileCopyrightText: 2023 - 2025 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

"""Minimal example of how to run an `~gymnasium.Env`.

This is used by :doc:`/guide/core` and :doc:`/guide/control_flow`.
"""

from fake_module import get_num_episodes, get_policy  # type: ignore[import-not-found]
from gymnasium import Env
from gymnasium.spaces import Box
from numpy import clip

from cernml import coi

policy = get_policy()
num_episodes = get_num_episodes()

# Limit steps per episode to prevent infinite loops.
env = coi.make("MyEnv-v0", max_episode_steps=10)
assert isinstance(env, Env)
with env:
    ac_space = env.action_space
    assert isinstance(ac_space, Box)

    for _ in range(num_episodes):
        terminated = truncated = False
        obs, info = env.reset()
        while not (terminated or truncated):
            action = policy.predict(obs)
            action = clip(action, ac_space.low, ac_space.high)
            obs, reward, terminated, truncated, info = env.step(action)
