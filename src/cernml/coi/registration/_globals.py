# SPDX-FileCopyrightText: 2020-2024 CERN
# SPDX-FileCopyrightText: 2023-2024 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

"""Definition of global variables and functions for this package."""

from __future__ import annotations

import typing as t

from ._registry import EnvRegistry
from ._spec import bump_stacklevel

if t.TYPE_CHECKING:
    from contextlib import AbstractContextManager

    from gymnasium import Env, Wrapper
    from gymnasium.experimental.vector import VectorEnv

    from .. import protocols
    from . import _base
    from ._spec import EnvSpec

__all__ = (
    "current_namespace",
    "make",
    "make_vec",
    "namespace",
    "pprint_registry",
    "register",
    "registry",
    "spec",
)


registry = EnvRegistry(ep_group="cernml.envs")


def current_namespace() -> str | None:
    """Return the current namespace as set by `namespace()`."""
    return registry.current_namespace


def namespace(ns: str) -> AbstractContextManager:
    """Context manager for modifying the current namespace."""
    return registry.namespace(ns)


def spec(env_id: str) -> EnvSpec:
    """Retrieve the `.EnvSpec` for a registered environment.

    Args:
        env_id: The environment ID in the usual format
            ``[<namespace>/]<name>[-v<version>]``.

    Returns:
        The environment spec.

    Raises:
        NotFoundError: if the spec cannot be found.
    """
    return registry.spec(env_id)


def pprint_registry(
    *,
    num_cols: int = 3,
    exclude_namespaces: list[str] | None = None,
    disable_print: bool = False,
) -> str | None:
    """Pretty print all environments in the `registry`.

    Keyword Args:
        num_cols: The number of columns in which to print the
            environments.
        exclude_namespaces: Optional. A list of namespaces to be
            excluded from printing.
        disable_print: If True, print nothing and return the message as
            a string instead.
    """
    return registry.pprint(
        num_cols=num_cols,
        exclude_namespaces=exclude_namespaces,
        disable_print=disable_print,
    )


@t.overload
def register(
    env_id: str,
    /,
    entry_point: type[protocols.Problem] | _base.EnvCreator | str,
    vector_entry_point: _base.VectorEnvCreator | str | None = None,
    *,
    reward_threshold: float | None = None,
    nondeterministic: bool = False,
    max_episode_steps: int | None = None,
    order_enforce: bool = True,
    autoreset: bool = False,
    disable_env_checker: bool = False,
    apply_api_compatibility: bool = False,
    additional_wrappers: tuple[_base.WrapperSpec, ...] = (),
    **kwargs: t.Any,
) -> None: ...


@t.overload
def register(
    env_id: str,
    /,
    *,
    vector_entry_point: _base.VectorEnvCreator | str,
    reward_threshold: float | None = None,
    nondeterministic: bool = False,
    max_episode_steps: int | None = None,
    order_enforce: bool = True,
    autoreset: bool = False,
    disable_env_checker: bool = False,
    apply_api_compatibility: bool = False,
    additional_wrappers: tuple[_base.WrapperSpec, ...] = (),
    **kwargs: t.Any,
) -> None: ...


def register(
    env_id: str,
    /,
    entry_point: type[protocols.Problem] | _base.EnvCreator | str | None = None,
    vector_entry_point: _base.VectorEnvCreator | str | None = None,
    *,
    reward_threshold: float | None = None,
    nondeterministic: bool = False,
    max_episode_steps: int | None = None,
    order_enforce: bool = True,
    autoreset: bool = False,
    disable_env_checker: bool = False,
    apply_api_compatibility: bool = False,
    additional_wrappers: tuple[_base.WrapperSpec, ...] = (),
    **kwargs: t.Any,
) -> None:
    """Register an environment for later use with `make()`.

    This function must be called exactly once for every optimization
    problem you want to create with `make()`.

    The environment ID follows the syntax:
    ``[<namespace>/]<name>[-v<version>]``. See `make()` for information
    how the namespace and version are used.

    Args:
        env_id: The ID to register the environment under.
        entry_point: The entry point for creating the environment. May
            be either a subclass of `~.coi.Problem`, a function that
            returns an instance of `~.coi.Problem`, or a string. If
            a string, it should be in the format ``<module>:<object>``
            with as many dots ``.`` on either side of the colon as
            necessary.
        reward_threshold: With a reward above this threshold, an agent
            is considered to have learnt the environment.
        nondeterministic: If True, the environment is nondeterministic;
            even with knowledge of the initial seed and all actions, the
            same state cannot be reached.
        max_episode_steps: If not None, the maximum number of steps before
            an episode is truncated. Implemented via
            `~gymnasium.wrappers.TimeLimit`.
        order_enforce: If True, a wrapper around the environment ensures
            that all functions are called in the correct order.
            Implemented via `~gymnasium.wrappers.OrderEnforcing`.
        autoreset: If True, a wrapper around the environment calls
            :func:`~gymnasium.Env.reset()` immediately whenever an
            episode ends. Implemented via
            `~gymnasium.wrappers.AutoResetWrapper`.
        disable_env_checker: Normally, all environments are wrapped in
            `~gymnasium.wrappers.PassiveEnvChecker`. If True, don't do that
            for this environment.
        apply_api_compatibility: If True, the class still follows the
            Gym v0.21 Step API. In this case,
            `~gymnasium.wrappers.StepAPICompatibility`
            wraps around it to ensure compatibility with the new API.
        additional_wrappers: Additional wrappers to apply the
            environment automatically when `make()` is called.
        vector_entry_point: The entry point for creating a *vector*
            environment. Used by `make_vec()`.
        **kwargs: Any further keyword arguments are passed to the
            environment itself upon initialization.
    """
    bump_stacklevel(kwargs)
    registry.register(
        env_id,
        entry_point=entry_point,
        vector_entry_point=vector_entry_point,
        reward_threshold=reward_threshold,
        nondeterministic=nondeterministic,
        max_episode_steps=max_episode_steps,
        order_enforce=order_enforce,
        autoreset=autoreset,
        disable_env_checker=disable_env_checker,
        apply_api_compatibility=apply_api_compatibility,
        additional_wrappers=additional_wrappers,
        **kwargs,
    )


def make(
    env_id: str | EnvSpec,
    /,
    *,
    max_episode_steps: int | None = None,
    autoreset: bool | None = None,
    apply_api_compatibility: bool | None = None,
    disable_env_checker: bool | None = None,
    order_enforce: bool | None = None,
    **kwargs: t.Any,
) -> protocols.Problem:
    """Create an environment according to the given ID.

    The environment must have been previously registered with
    `cernml.coi.register()`.

    To find all available environments, use `registry.all()
    <.EnvRegistry.all>`.

    Unlike in `register()`, the env ID may follow the syntax
    ``"[<module>:][<namespace>/]<name>[-v<version>]"``. If a module is
    given, it is imported unconditionally before looking up the
    environment.

    In addition, if you don't specify the version of an environment that
    has been registered with a version, the *highest version* is picked
    automatically.

    If a namespace is given and the environment cannot be found
    immediately, an :doc:`entry point <pkg:specifications/entry-points>`
    in the group ``cernml.envs`` with the same name as the namespace is
    loaded. If the entry point points at a module, it is imported; if it
    points at a function, the function is called. The function should do
    nothing but call `register()` as necessary.

    Args:
        env_id: Name of the environment or an `~.EnvSpec`.
        max_episode_steps: Override the same parameter of `register()`.
            Implemented via `~gymnasium.wrappers.TimeLimit`.
        autoreset: If True, to automatically reset the environment after
            each episode. Implemented via
            `~gymnasium.wrappers.AutoResetWrapper`.
        apply_api_compatibility: Override the same parameter of
            `register()`. Implemented via
            `~gymnasium.wrappers.StepAPICompatibility`.
        disable_env_checker: Override the same parameter of
            `register()`. Implemented via
            `~gymnasium.wrappers.PassiveEnvChecker`.
        order_enforce: Override the same parameter of
            `register()`. Implemented via
            `~gymnasium.wrappers.OrderEnforcing`.
        kwargs: Additional arguments to pass to the environment
            constructor.

    Returns:
        An instance of the environment with wrappers applied.

    Raises:
        RegistryError: if the given ID doesn't exist or the environment
            constructor failed.
    """
    bump_stacklevel(kwargs)
    return registry.make(
        env_id,
        max_episode_steps=max_episode_steps,
        autoreset=autoreset,
        apply_api_compatibility=apply_api_compatibility,
        disable_env_checker=disable_env_checker,
        order_enforce=order_enforce,
        **kwargs,
    )


def make_vec(
    env_id: str | EnvSpec,
    /,
    *,
    num_envs: int = 1,
    vectorization_mode: str = "async",
    vector_kwargs: dict[str, t.Any] | None = None,
    wrappers: t.Sequence[t.Callable[[Env], Wrapper]] | None = None,
    **kwargs: t.Any,
) -> VectorEnv:
    """Create a *vector* environment according to the given ID.

    Note:
        This is a thin wrapper around ``gymnasium.make_vec()``. The only
        difference is that it looks up environments in the COI registry
        instead of the Gym registry.

        In Gymnasium, this feature is still considered experimental and
        likely to change in future releases.

    To find all available environments, use `registry.all()
    <.EnvRegistry.all>`.

    Unlike in `register()`, the env ID may follow the syntax
    ``"[<module>:][<namespace>/]<name>[-v<version>]"``. If a module is
    given, it is imported before looking up the environment.

    In addition, if you don't specify the version of an environment that
    has been registered with a version, the *highest version* is picked
    automatically.

    Args:
        env_id: Name of the environment or an `.EnvSpec`.
        num_envs: Number of environments to create.
        vectorization_mode: How to vectorize the environment. Can be
            either ``"async"``, ``"sync"`` or ``"custom"``.
        vector_kwargs: Additional arguments to pass to the vectorized
            environment constructor.
        wrappers: A sequence of wrapper functions to apply to the
            environment. Can only be used in *sync* or *async* mode.
        **kwargs: Additional arguments to pass to the environment
            constructor.

    Returns:
        An instance of the environment.

    Raises:
        RegistryError: if the given ID doesn't exist or the environment
            constructor failed.
    """
    bump_stacklevel(kwargs)
    return registry.make_vec(
        env_id,
        num_envs=num_envs,
        vectorization_mode=vectorization_mode,
        vector_kwargs=vector_kwargs,
        wrappers=wrappers,
        **kwargs,
    )
