# SPDX-FileCopyrightText: 2016 OpenAI
# SPDX-FileCopyrightText: 2020 - 2025 CERN
# SPDX-FileCopyrightText: 2022 - 2025 Farama Foundation
# SPDX-FileCopyrightText: 2023 - 2025 GSI Helmholtzzentrum für Schwerionenforschung
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

See the page :doc:`/guide/registration` for a more detailed description
of the concepts.

This mechanism is largely copied from the :doc:`gym:api/registry`
mechanism of Gymnasium. Adjustments have been made here and there to
accommodate `~cernml.coi.Problem` and its non-Env subclasses.

**General changes:**
    - Compatibility with Python 3.8 has been dropped.

    - This registry uses the entry point ``cernml.envs`` to load
      plugins.

    - Plugins using the :doc:`entrypoints
      <pkg:specifications/entry-points>` mechanism are not registered
      immediately upon import of this package. Instead, they're only
      loaded the first time that something from their namespace is
      requested.

    - All warnings issued use the `stacklevel <std:warnings.warn>`
      argument to trace themselves back to the line that calls
      `~.coi.register()` or `~.coi.make()`. This makes it easier to find
      their source.

    - Instead of ``gymnasium.Error``, a dedicated type hierarchy is used
      for both exceptions and warnings. All types are exposed in the
      `cernml.coi.registration.errors` module.

    - General code cleanup.

**Specific changes** to `~cernml.coi.make()`:
    - `isinstance` checks of *env_spec* and *env_creator.metadata* have
      been removed or adjusted.

    - The parameter *order_enforce* has been added with the same
      override semantics as *disable_env_checker*.

    - A warning about the deprecated `~cernml.coi.Problem.metadata` key
      ``"render.modes"`` has been added.

    - Wrappers are only added if the wrapped environment is actually
      a `gymnasium.Env`, to keep `~cernml.coi.SingleOptimizable` and
      others safe.

    - The *stacklevel* parameter of :func:`warnings.warn()` is threaded
      through the functions so that any warning is attributed to the
      code that called into COI (and not COI itself).
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
