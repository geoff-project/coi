# SPDX-FileCopyrightText: 2020-2024 CERN
# SPDX-FileCopyrightText: 2023-2024 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

"""These functions allow you to search and lazy-load problems.

All optimization problems should be `registered <.coi.register>` exactly
once. The most common way to register an optimization problem is
immediately after definition. Registering your problem allows downstream
users to instantiate them in a convenient and uniform manner:

    >>> from cernml import coi
    >>> class MyOptProblem(coi.SingleOptimizable):
    ...     optimization_space = ...
    ...     def get_initial_params(self): ...
    ...     def compute_single_objective(self, params): ...
    ...
    >>> coi.register("MyOptProblem-v1", entry_point=MyOptProblem)
    ...
    >>> env = coi.make("MyOptProblem-v1")

See the page :doc:`/guide/registry` for a more detailed description of
the concepts.

This mechanism is largely copied from the :doc:`gym:api/registry`
mechanism of Gymnasium. Adjustments have been made here and there to
accommodate `~cernml.coi.Problem` and its non-Env subclasses. Two
notable changes are:

- All warnings issued use the `stacklevel <std:warnings.warn>` argument
  to trace themselves back to the line that calls `~.coi.register()` or
  `~.coi.make()`. This makes it easier to find their source.
- Plugins using the :doc:`entrypoints <pkg:specifications/entry-points>`
  mechanism are not registered immediately upon import of this package.
  Instead, they're only loaded the first time that something from their
  namespace is requested.
- The entrypoint used by this registry is ``cernml.envs``.
"""

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
