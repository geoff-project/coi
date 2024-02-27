# SPDX-FileCopyrightText: 2020-2024 CERN
# SPDX-FileCopyrightText: 2023-2024 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

"""Forwarding to the Gymnasium Registry.

Temporary note: Before Gym 0.22, we used to maintain our own registry.
We need to investigate how best to proceed -- does it make sense to just
put everything into one registry?
"""

from gymnasium.envs.registration import (
    EnvCreator,
    EnvSpec,
    VectorEnvCreator,
    WrapperSpec,
    current_namespace,
    make,
    make_vec,
    pprint_registry,
    register,
    register_envs,
    registry,
    spec,
)

__all__ = (
    "EnvCreator",
    "EnvSpec",
    "VectorEnvCreator",
    "WrapperSpec",
    "current_namespace",
    "make",
    "make_vec",
    "pprint_registry",
    "register",
    "register_envs",
    "registry",
    "spec",
)
