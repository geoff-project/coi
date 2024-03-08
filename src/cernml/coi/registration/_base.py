# SPDX-FileCopyrightText: 2020-2024 CERN
# SPDX-FileCopyrightText: 2023-2024 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

"""Safe imports from the Gymnasium registry module.

This imports all helpers that do not reference the global
`gymnasium.envs.registry` object. Those are functions we can reuse in
our own implementation.
"""

from gymnasium.envs.registration import (
    EnvCreator,
    EnvSpec,
    VectorEnvCreator,
    WrapperSpec,
    get_env_id,
    load_env_creator,
    parse_env_id,
    pprint_registry,
    register_envs,
)

__all__ = (
    "EnvCreator",
    "EnvSpec",
    "VectorEnvCreator",
    "WrapperSpec",
    "get_env_id",
    "load_env_creator",
    "parse_env_id",
    "pprint_registry",
    "register_envs",
)
