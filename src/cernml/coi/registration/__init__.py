# SPDX-FileCopyrightText: 2020-2024 CERN
# SPDX-FileCopyrightText: 2023-2024 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

"""Replication of the Gymnasium Registry."""

from . import errors
from ._base import (
    EnvCreator,
    VectorEnvCreator,
    WrapperSpec,
    get_env_id,
    load_env_creator,
    parse_env_id,
    register_envs,
)
from ._globals import (
    current_namespace,
    make,
    make_vec,
    namespace,
    pprint_registry,
    register,
    registry,
    spec,
)
from ._registry import EnvRegistry
from ._spec import EnvSpec, MinimalEnvSpec, downcast_spec

__all__ = (
    "EnvCreator",
    "EnvRegistry",
    "EnvSpec",
    "MinimalEnvSpec",
    "VectorEnvCreator",
    "WrapperSpec",
    "current_namespace",
    "downcast_spec",
    "errors",
    "get_env_id",
    "load_env_creator",
    "make",
    "make_vec",
    "namespace",
    "parse_env_id",
    "pprint_registry",
    "register",
    "register_envs",
    "registry",
    "spec",
)
