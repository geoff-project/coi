# SPDX-FileCopyrightText: 2020-2024 CERN
# SPDX-FileCopyrightText: 2023-2024 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

"""Definition of the `EnvRegistry` class."""

from __future__ import annotations

import contextlib
import importlib
import operator as op
import typing as t
import warnings

from gymnasium import make_vec as make_vec_impl

from . import _base, errors
from ._make import make as make_impl
from ._plugins import Plugins
from ._sentinel import MISSING, Sentinel
from ._spec import EnvSpec, bump_stacklevel, downcast_spec
from ._specdict import EnvSpecDict, raise_env_not_found

if t.TYPE_CHECKING:
    from contextlib import AbstractContextManager

    import gymnasium.experimental.vector

    from .. import protocols

__all__ = ("EnvRegistry",)


class EnvRegistry:
    """Class of the environment `.registry`.

    Note that this package uses its own registry, which is independent
    of Gymnasium's `~gymnasium.envs.registration.registry`. An
    environment registered via :func:`gymnasium.register()` is not
    findable via `cernml.coi.make()` and vice versa.

    To create your own, local registry, simply instantiate this class
    again.

    Args:
        ep_group: Optional. If passed, a string with the :doc:`entry point
            <pkg:specifications/entry-points>` group that should be used
            for namespace lookups. If not passed, no entry points are
            used to dynamically load environments.
    """

    def __init__(self, ep_group: str | None = None) -> None:
        self._plugins = Plugins(ep_group)
        self._registry = EnvSpecDict()

    @property
    def current_namespace(self) -> str | None:
        """The current namespace as set by `namespace()`."""
        return vars(self).get("current_namespace")

    @contextlib.contextmanager
    def namespace(self, ns: str, /) -> t.Iterator[None]:
        """Context manager for modifying the current namespace."""
        old_ns = vars(self).get("current_namespace")
        vars(self)["current_namespace"] = ns
        try:
            yield
        finally:
            vars(self)["current_namespace"] = old_ns

    def all(
        self,
        *,
        ns: str | None | Sentinel = MISSING,
        name: str | Sentinel = MISSING,
        version: int | bool | None | Sentinel = MISSING,
    ) -> t.Iterator[EnvSpec]:
        """Yield all environment specs that match a given filter.

        When called without arguments, an iterator of all environment
        specs is returned. Any parameter that is passed adds a filter on
        either the namespace, the name, or the version of the yielded
        specs.

        Args:
            ns: If passed and a string, only environment specs with that
                namespace are yielded. If passed and None, only
                environment specs *without* a namespace are yielded.
            name: If passed and a string, only environment specs with
                the given name are yielded.
            version: If passed and an integer, only environment specs
                with that exact version are yielded. If passed and True,
                only environment specs that have *any* version are
                yielded. If passed and False or None, only environment
                specs *without* a version are yielded.
        """
        return self._registry.select(ns=ns, name=name, version=version)

    def spec(self, env_id: str, /) -> EnvSpec:
        """Implementation of `~.coi.spec()`."""  # noqa: D402
        env_spec = self._registry.get(env_id)
        if env_spec is None:
            raise_env_not_found(EnvSpec(env_id), self._registry)
        return env_spec

    def pprint(
        self,
        *,
        num_cols: int = 3,
        exclude_namespaces: list[str] | None = None,
        disable_print: bool = False,
    ) -> str | None:
        """Implementation of `~.coi.pprint_registry()`."""
        return _base.pprint_registry(
            print_registry=t.cast(dict[str, _base.EnvSpec], self._registry),
            num_cols=num_cols,
            exclude_namespaces=exclude_namespaces,
            disable_print=disable_print,
        )

    def register(
        self,
        env_id: str,
        /,
        entry_point: type[protocols.Problem] | _base.EnvCreator | str | None = None,
        vector_entry_point: _base.VectorEnvCreator | str | None = None,
        **kwargs: t.Any,
    ) -> None:
        """Implementation of `~.coi.register()`."""  # noqa: D402
        stacklevel = kwargs.pop("stacklevel", 2)
        if entry_point is None and vector_entry_point is None:
            raise ValueError(
                "either `entry_point` or `vector_entry_point` must be provided"
            )
        env_id = self._normalize_namespace(
            env_id, nsarg=kwargs.pop("namespace", None), stacklevel=1 + stacklevel
        )
        new_spec = EnvSpec(
            id=env_id,
            entry_point=t.cast(_base.EnvCreator, entry_point),
            vector_entry_point=vector_entry_point,
            **kwargs,
        )
        self._check_spec_register(new_spec)
        if new_spec.id in self._registry:
            warnings.warn(
                errors.EnvSpecExistsWarning(env_id=new_spec.id), stacklevel=stacklevel
            )
        self._registry[new_spec.id] = new_spec

    def make(
        self,
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
        """Implementation of `~.coi.make()`."""  # noqa: D402
        stacklevel = bump_stacklevel(kwargs)
        allow_imports = kwargs.pop("allow_imports", True)
        if isinstance(env_id, EnvSpec):
            env_spec = env_id
        else:
            env_spec = self._find_spec(
                env_id, allow_imports=allow_imports, stacklevel=1 + stacklevel
            )
        return make_impl(
            env_spec,
            max_episode_steps=max_episode_steps,
            autoreset=autoreset,
            apply_api_compatibility=apply_api_compatibility,
            disable_env_checker=disable_env_checker,
            order_enforce=order_enforce,
            **kwargs,
        )

    def make_vec(
        self,
        env_id: str | EnvSpec,
        /,
        num_envs: int = 1,
        vectorization_mode: str = "async",
        vector_kwargs: dict[str, t.Any] | None = None,
        wrappers: (
            t.Sequence[t.Callable[[gymnasium.Env], gymnasium.Wrapper]] | None
        ) = None,
        **kwargs: t.Any,
    ) -> gymnasium.experimental.vector.VectorEnv:
        """Implementation of `~.coi.make_vec()`."""  # noqa: D402
        stacklevel = kwargs.pop("stacklevel", 2)
        allow_imports = kwargs.pop("allow_imports", True)
        if isinstance(env_id, EnvSpec):
            env_spec = env_id
        else:
            env_spec = self._find_spec(
                env_id, allow_imports=allow_imports, stacklevel=1 + stacklevel
            )
        # Because we pass an `EnvSpec` and not a string, we can be sure
        # that Gymnasium will not consult its own registry.
        return make_vec_impl(
            downcast_spec(env_spec),
            num_envs=num_envs,
            vectorization_mode=vectorization_mode,
            vector_kwargs=vector_kwargs,
            wrappers=wrappers,
            **kwargs,
        )

    def _check_spec_register(self, spec: EnvSpec) -> None:
        """Checks whether the spec is valid to be registered.

        Helper function for `register`.
        """
        unversioned_spec = next(
            self._registry.select(ns=spec.namespace, name=spec.name, version=False),
            None,
        )
        if unversioned_spec and spec.version is not None:
            raise errors.UnversionedExistsError(spec, unversioned_spec)
        latest_versioned_spec = max(
            self._registry.select(ns=spec.namespace, name=spec.name, version=True),
            key=op.attrgetter("version"),
            default=None,
        )
        if latest_versioned_spec and spec.version is None:
            raise errors.VersionedExistsError(spec, latest_versioned_spec)

    def _normalize_namespace(
        self, env_id: str, /, *, nsarg: str | None, stacklevel: int
    ) -> str:
        """Take all three sources of namespaces into account.

        Priority is as follows:

        - `~EnvRegistry.current_namespace` always wins;
        - if that is None but *env_id* contains a namespace, this one is
          used;
        - even if a keyword argument *namespace* is passed to
          `register()`, we never use it. It exists for backward
          compatibility and we only warn if it is passed and different
          from `~EnvRegistry.current_namespace`.
        """
        ns, name, version = _base.parse_env_id(env_id)
        current_ns = self.current_namespace
        if current_ns is not None:
            ns = current_ns
            if nsarg is not None and nsarg != current_ns:
                warnings.warn(
                    errors.AmbiguousNamespaceWarning(
                        arg_ns=nsarg, current_ns=current_ns
                    ),
                    stacklevel=stacklevel,
                )
        return _base.get_env_id(ns, name, version)

    def _find_spec(
        self, env_id: str, /, *, allow_imports: bool, stacklevel: int
    ) -> EnvSpec:
        """Find a spec with the given ID in the registry.

        If *allow_imports* is True, plugins that provide the env's
        namespace may be loaded and a ``{module}:`` prefix of *env_id*
        may be resolved, if present.
        """
        if not isinstance(env_id, str):
            raise TypeError(f"not a string: {env_id!r}")
        env_name = _strip_and_import_module(env_id, allow_imports=allow_imports)
        # Attempt plain lookup. Either we find the spec immediately, or
        # we retry after loading plugins. In either case, `min_spec`
        # contains the results of parsing `env_name`.
        matching_spec = self._registry.get(env_name)
        if matching_spec is not None:
            min_spec = matching_spec
        else:
            min_spec = EnvSpec(env_name)
            if min_spec.namespace in self._plugins.unloaded and allow_imports:
                self._load_namespace(min_spec.namespace, stacklevel=1 + stacklevel)
            matching_spec = self._registry.get(env_name)
        # At this stage, there are three options:
        # 1. we found a spec _will_ use it. We still want to warn about
        #    outdated versions.
        # 2. we didn't find a spec because the user wants us to find the
        #    latest version.
        # 3. The env plain doesn't exist.
        latest_spec = self._try_upgrade_spec(min_spec, stacklevel=1 + stacklevel)
        if matching_spec:
            return matching_spec
        if latest_spec:
            return latest_spec
        return raise_env_not_found(min_spec, self._registry)

    def _load_namespace(self, ns: str, /, *, stacklevel: int) -> None:
        """Load all plugins that contribute to the given namespace."""
        context: AbstractContextManager = self.namespace(ns)
        if ns in ("__root__", "__internal__"):
            context = contextlib.nullcontext()
        elif ns.startswith("__") and ns.endswith("__"):
            warnings.warn(
                errors.GymDeprecationWarning(f"namespace {ns!r}", "'__root__'"),
                stacklevel=stacklevel,
            )
        with context:
            self._plugins.load(ns, stacklevel=1 + stacklevel)

    def _try_upgrade_spec(self, spec: EnvSpec, *, stacklevel: int) -> EnvSpec | None:
        latest_spec = max(
            self._registry.select(ns=spec.namespace, name=spec.name, version=True),
            key=op.attrgetter("version"),
            default=None,
        )
        if latest_spec is None:
            # Env doesn't exist or is generally unversioned.
            return None
        assert latest_spec.version is not None, latest_spec
        if spec.version is not None:
            if latest_spec.version > spec.version:
                warnings.warn(
                    errors.EnvOutOfDateWarning(spec.id, latest_spec.version),
                    stacklevel=stacklevel,
                )
            return None
        warnings.warn(
            errors.EnvUpgradedWarning(spec.id, latest_spec.version),
            stacklevel=stacklevel,
        )
        return latest_spec


def _strip_and_import_module(env_id: str, /, *, allow_imports: bool) -> str:
    """Remove *module* portion from an env ID.

    If *allow_imports* is True, the stripped module is imported by name.
    """
    module, env_name = _split_module(env_id)
    if module is not None:
        if not allow_imports:
            raise errors.EnvImportError(
                "imports have been disabled", module=module, env_name=env_name
            )
        try:
            importlib.import_module(module)
        except ModuleNotFoundError:
            raise
        except Exception as exc:
            raise errors.EnvImportError(module=module, env_name=env_name) from exc
    return env_name


def _split_module(env_id: str, /) -> tuple[str | None, str]:
    module, sep, name = env_id.partition(":")
    if sep:
        return module, name
    return None, module
