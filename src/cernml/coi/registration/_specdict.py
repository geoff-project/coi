# SPDX-FileCopyrightText: 2016 OpenAI
# SPDX-FileCopyrightText: 2022 Farama Foundation
# SPDX-FileCopyrightText: 2020-2024 CERN
# SPDX-FileCopyrightText: 2023-2024 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

"""Finding specs and reasons why they weren't found."""

from __future__ import annotations

import difflib
import operator as op
import typing as t
from functools import partial
from io import StringIO
from operator import attrgetter

from . import errors
from ._base import get_env_id
from ._sentinel import MISSING, Sentinel

if t.TYPE_CHECKING:
    from ._spec import EnvSpec

__all__ = (
    "EnvSpecDict",
    "EnvSpecMapping",
    "raise_env_not_found",
)


class EnvSpecMapping(t.Mapping[str, "EnvSpec"]):
    """A mapping from environment IDs to specs.

    This is a regular `~typing.Mapping` enhanced with a single method,
    `select()`.
    """

    def select(
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
        if version is MISSING:
            check_version = partial(op.is_not, MISSING)
        elif version is True:
            check_version = partial(op.is_not, None)
        elif version is False or version is None:
            check_version = partial(op.is_, None)
        else:
            check_version = partial(op.eq, version)
        return (
            spec
            for spec in self.values()
            if (ns is MISSING or spec.namespace == ns)
            and (name is MISSING or spec.name == name)
            and check_version(spec.version)
        )


class EnvSpecDict(dict[str, "EnvSpec"], EnvSpecMapping):
    """A `dict` subclass that provides a method `select()`."""


def raise_env_not_found(bad_spec: EnvSpec, all_specs: EnvSpecMapping) -> t.NoReturn:
    """Raise an informative exception if an environment can't be found.

    This investigates each part of the environment ID and enhances the
    exception message with hints, e.g. which part of the ID failed to
    bring any candidates, or whether there are similarly named
    environments.

    This function *always* raises an exception.

    Raises:
        NamespaceNotFoundError: if no environments with the given
            namespace exist.
        NameNotFoundError: if not environments with the given namespace
            and name exist.
        VersionNotFoundError: if environments with the given namespace
            and name exist, but all versions are lower than the
            requested one.
        DeprecatedEnv: if either you requested a versioned environment
            when only an unversioned default exists, or if the requested
            version doesn't exist but a *higher* one does.
        NotFoundError: if none of the above apply. All above exceptions
            are subclasses of this one.
    """
    _raise_bad_ns(bad_spec.namespace, all_specs)
    _raise_bad_name(bad_spec.namespace, bad_spec.name, all_specs)
    _raise_bad_version(bad_spec.namespace, bad_spec.name, bad_spec.version, all_specs)


def _raise_bad_ns(ns: str | None, all_specs: EnvSpecMapping) -> None:
    if ns is None:
        return
    namespaces = {spec.namespace for spec in all_specs.values() if spec.namespace}
    if ns in namespaces:
        return
    if suggestion := difflib.get_close_matches(ns, namespaces, n=1):
        suggestion_msg = f"Did you mean: `{suggestion[0]}`?"
    else:
        suggestion_msg = f"Have you installed the proper package for {ns}?"
    raise errors.NamespaceNotFoundError(f"Namespace {ns} not found. {suggestion_msg}")


def _raise_bad_name(ns: str | None, name: str, all_specs: EnvSpecMapping) -> None:
    names = {spec.name for spec in all_specs.select(ns=ns)}
    if name in names:
        return
    suggestion = difflib.get_close_matches(name, names, n=1)
    namespace_msg = f" in namespace {ns}" if ns else ""
    suggestion_msg = f" Did you mean: `{suggestion[0]}`?" if suggestion else ""
    raise errors.NameNotFoundError(
        f"Environment `{name}` doesn't exist{namespace_msg}.{suggestion_msg}"
    )


def _raise_bad_version(
    ns: str | None, name: str, version: int | None, all_specs: EnvSpecMapping
) -> t.NoReturn:
    message = StringIO()
    if version is not None:
        message.write(
            f"Environment version `v{version}` for "
            f"environment `{get_env_id(ns, name, None)}` doesn't exist."
        )
    else:
        # We can hit this case if using `EnvRegistry.spec()`, since it
        # doesn't do automatic version resolution for unversioned envs.
        message.write(
            f"Unversioned environment `{get_env_id(ns, name, None)}` doesn't exist."
        )
    versioned_specs = sorted(
        all_specs.select(ns=ns, name=name, version=True), key=attrgetter("version")
    )
    default_spec = next(all_specs.select(ns=ns, name=name, version=False), None)
    if default_spec:
        message.write(f" It provides the default version `{default_spec.id}`.")
    if not versioned_specs:
        raise errors.DeprecatedEnv(message.getvalue())
    # We use that `versioned_specs` is already sorted.
    latest_spec = versioned_specs[-1]
    assert latest_spec.version is not None, latest_spec
    if version is not None and latest_spec.version > version:
        message.write(f" Please use `{latest_spec.id}` instead.")
        raise errors.DeprecatedEnv(message.getvalue())
    # At this point, we know that namespace and name match, and we found
    # at least some other versions.
    message.write(" It provides versioned environments: [ ")
    message.write(", ".join(f"`v{env_spec.version}`" for env_spec in versioned_specs))
    message.write(" ].")
    raise errors.VersionNotFoundError(message.getvalue())
