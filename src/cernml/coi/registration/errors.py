# SPDX-FileCopyrightText: 2020-2024 CERN
# SPDX-FileCopyrightText: 2023-2024 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

"""Exceptions raised by this package."""

from __future__ import annotations

import typing as t

if t.TYPE_CHECKING:
    from .._problem import Problem
    from ._base import WrapperSpec
    from ._spec import EnvSpec

__all__ = (
    "AmbiguousNamespaceWarning",
    "ApiCompatError",
    "DeprecatedEnv",
    "EntryPointError",
    "EnvImportError",
    "EnvOutOfDateWarning",
    "EnvSpecExistsWarning",
    "EnvUpgradedWarning",
    "EnvUpgradedWarning",
    "GymDeprecationWarning",
    "HumanRenderingError",
    "HumanRenderingWarning",
    "NameNotFoundError",
    "NamespaceNotFoundError",
    "NotFoundError",
    "PluginWarning",
    "RegistrationError",
    "RegistryError",
    "RegistryWarning",
    "RenderModeWarning",
    "TypeWarning",
    "UnversionedExistsError",
    "VersionNotFoundError",
    "VersionedExistsError",
    "WrapperClassError",
    "WrapperError",
    "WrapperMismatchError",
    "WrapperUnexpectedError",
)


class RegistryError(Exception):
    """An error occurred in the `EnvRegistry`."""


class EntryPointError(RegistryError, TypeError):
    """No entry point found."""


class HumanRenderingError(RegistryError, TypeError):
    """The `HumanRendering` wrapper couldn't be created."""

    def __init__(self, env_id: str) -> None:
        super().__init__(
            f"You passed render_mode='human' although {env_id} "
            f"doesn't implement human-rendering natively. Gym "
            f"tried to apply the HumanRendering wrapper but it "
            f"looks like your environment is using the old "
            f"rendering API, which is not supported by the "
            f"HumanRendering wrapper."
        )


class EnvImportError(RegistryError, ImportError):
    """Could not import a module required to load an environment."""

    def __init__(self, msg: str = "", *, module: str, env_name: str) -> None:
        prefix = f"could not import module {module!r} to make env {env_name!r}"
        msg = f"{prefix}: {msg}" if msg else prefix
        super().__init__(msg)
        self.module = module
        self.env_name = env_name


class ApiCompatError(RegistryError, TypeError):
    """Step API Compatibility wrapper applied to incompatible env."""

    def __init__(self, *args: t.Any, problem: Problem) -> None:
        if args:  # pragma: no cover
            super.__init__(*args)
        else:
            super().__init__(
                f"attempt to apply API compatibility layer "
                f"to non-legacy env: {problem!r}"
            )


class RegistrationError(RegistryError):
    """An error occurred while registering an env."""


class UnversionedExistsError(RegistrationError):
    """Tried to register a versioned env where an unversioned exists."""

    def __init__(self, spec: EnvSpec, unversioned: EnvSpec) -> None:
        super().__init__(
            f"Can't register the versioned environment "
            f"`{spec.id}` when the unversioned environment "
            f"`{unversioned.id}` of the same name already exists."
        )
        self.spec = spec
        self.unversioned = unversioned


class VersionedExistsError(RegistrationError):
    """Tried to register an unversioned env where a versioned exists."""

    def __init__(self, spec: EnvSpec, latest: EnvSpec) -> None:
        super().__init__(
            f"Can't register the unversioned environment "
            f"`{spec.id}` when the versioned environment "
            f"`{latest.id}` of the same name already exists. "
            f"Note: the default behavior is that `gym.make` with "
            f"the unversioned environment will return the latest "
            f"versioned environment"
        )
        self.spec = spec
        self.latest = latest


class WrapperError(RegistryError, ValueError):
    """Recreating a wrapper went wrong."""

    spec: WrapperSpec


class WrapperClassError(WrapperError):
    """Attempt to load a wrapper without `RecordConstructorArgs`."""

    def __init__(self, name: str, /) -> None:
        super().__init__(
            f"{name} wrapper does not inherit from "
            f"`gymnasium.utils.RecordConstructorArgs`, "
            f"therefore, the wrapper cannot be recreated."
        )
        self.name = name


class WrapperUnexpectedError(WrapperError):
    """The entry point created more wrappers than specified."""

    def __init__(self, spec: WrapperSpec, /) -> None:
        super().__init__(f"entry point created an unexpected wrapper: {spec}")
        self.spec = spec


class WrapperMismatchError(WrapperError):
    """A specified wrapper differed from its spec."""

    def __init__(self, *, expected: WrapperSpec, actual: WrapperSpec) -> None:
        super().__init__(
            f"The environment's wrapper spec {actual} is different "
            f"from the saved `EnvSpec` additional wrapper {expected}"
        )
        self.spec = actual
        self.expected = expected


class RegistryWarning(UserWarning):
    """A warning emitted by the `EnvRegistry`."""


class EnvSpecExistsWarning(RegistryWarning, RuntimeWarning):
    """Two environments are using the same ID string."""

    def __init__(self, *args: t.Any, env_id: str) -> None:
        if args:  # pragma: no cover
            super().__init__(*args)
        else:
            super().__init__(
                f"Overriding environment {env_id} already in registry.",
            )
            self.env_id = env_id


class AmbiguousNamespaceWarning(RegistryWarning, RuntimeWarning):
    """An env spec is given a namespace via two different means."""

    def __init__(self, *args: str, current_ns: str, arg_ns: str) -> None:
        if args:  # pragma: no cover
            super().__init__(*args)
        else:
            super().__init__(
                f"Custom namespace {arg_ns!r} is being overridden "
                f"by current namespace {current_ns!r}. If you "
                f"are developing a plugin, you shouldn't specify "
                f"a namespace in `register()`. The namespace is "
                f"specified by the entry point in the "
                f"package metadata."
            )
        self.current_ns = current_ns
        self.arg_ns = arg_ns


class TypeWarning(RegistryWarning, RuntimeWarning):
    """An object has an unexpected type or attribute."""


class RenderModeWarning(RegistryWarning):
    """The user chose an incompatible render mode."""

    def __init__(
        self, msg: str = "", *, selected_mode: str, supported_modes: frozenset[str]
    ) -> None:
        if not msg:
            msg = (
                f"The environment is being initialized with render_mode="
                f"{selected_mode!r}, which is not among the possible "
                f"render_modes ({supported_modes})."
            )
        super().__init__(msg)
        self.selected_mode = selected_mode
        self.supported_modes = supported_modes


class HumanRenderingWarning(RenderModeWarning):
    """A missing ``human`` rendering mode is being adapted via wrapper."""

    def __init__(self, *, supported_modes: frozenset[str]) -> None:
        super().__init__(
            "You are trying to use 'human' rendering for an "
            "environment that doesn't natively support it. "
            "The HumanRendering wrapper is being applied to your "
            "environment.",
            selected_mode="human",
            supported_modes=supported_modes,
        )


class PluginWarning(RegistryWarning, RuntimeWarning):
    """A plugin failed to load."""

    def __init__(self, name: str, value: str, extra: str = "") -> None:
        if extra:
            super().__init__(f"plugin {name} ({value}) could not be loaded: {extra}")
        else:  # pragma: no cover
            super().__init__(f"plugin {name} ({value}) could not be loaded")
        self.name = name
        self.value = value


class EnvOutOfDateWarning(RegistryWarning, DeprecationWarning):
    """An env has been loaded with a lower version than is available."""

    def __init__(self, name: str, latest_version: int) -> None:
        super().__init__(
            f"The environment {name} is out of date. You should "
            f"consider upgrading to version `v{latest_version}`."
        )
        self.name = name
        self.latest_version = latest_version


class EnvUpgradedWarning(RegistryWarning):
    """An unversioned env ID has been replaced with its latest version."""

    def __init__(self, name: str, latest_version: int) -> None:
        super().__init__(
            f"Using the latest version v{latest_version} "
            f"for the unversioned environment `{name}`."
        )
        self.name = name
        self.latest_version = latest_version


class GymDeprecationWarning(RegistryWarning, DeprecationWarning):
    """Warning about feature to be removed in Gymnasium 1.0."""

    def __init__(self, name: str, replacement: str = "", /) -> None:
        if replacement:
            super().__init__(
                f"{name} is deprecated and will be removed in Gymnasium v1.0; "
                f"instead, use {replacement}"
            )
        else:
            super().__init__(
                f"{name} is deprecated and will be removed in Gymnasium v1.0"
            )
        self.name = name


class NotFoundError(RegistryError):
    """Env spec couldn't be found."""


class NamespaceNotFoundError(NotFoundError):
    """Env spec namespace couldn't be found."""


class NameNotFoundError(NotFoundError):
    """Env spec name couldn't be found."""


class VersionNotFoundError(NotFoundError):
    """Env spec version couldn't be found."""


class DeprecatedEnv(NotFoundError):
    """The env doesn't use versioning, but user passed a version."""
