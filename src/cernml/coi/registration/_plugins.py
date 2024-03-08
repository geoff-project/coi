# SPDX-FileCopyrightText: 2020-2024 CERN
# SPDX-FileCopyrightText: 2023-2024 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

"""Helper class to load entry points on demand."""

from __future__ import annotations

import sys
import traceback
import warnings
from functools import cached_property

from .errors import PluginWarning

if sys.version_info < (3, 10):
    import importlib_metadata
else:
    import importlib.metadata as importlib_metadata

__all__ = ("Plugins",)


class Plugins:
    """Simple entry point manager for `EnvRegistry`.

    This manager splits all entry points in the given group based on
    their names. It ensures that every entry point is loaded and called
    at most once.
    """

    def __init__(self, group: str | None) -> None:
        self._group = group
        self._loaded: set[str] = set()

    def __str__(self) -> str:
        nscount = len(self._unloaded_plugins) + len(self._loaded)
        return f"<plugins in {nscount} namespaces (loaded: {sorted(self._loaded)})>"

    def load(self, ns: str, *, stacklevel: int = 2) -> None:
        """Load the given namespace.

        If it has already been attempted to load before, this does
        nothing. If the namespace hasn't been loaded but there are no
        plugins for it, this does nothing as well.

        The *stacklevel* parameter is forwarded to `warnings.warn()`.
        The default value assigns a warning to the caller of `load()` if
        a plugin raises an exception while loading.
        """
        plugins = self._unloaded_plugins.pop(ns, None)
        if plugins is None:
            return
        for plugin in plugins:
            try:
                _load_plugin(plugin)
            except Exception:  # noqa: PERF203
                warnings.warn(
                    PluginWarning(plugin.name, plugin.value, traceback.format_exc()),
                    stacklevel=stacklevel,
                )
        self._loaded.add(ns)

    @property
    def unloaded(self) -> frozenset[str]:
        """Return the set of namespaces that aren't loaded yet."""
        return frozenset(self._unloaded_plugins)

    @property
    def loaded(self) -> frozenset[str]:
        """Return the set of namespaces that have been loaded."""
        return frozenset(self._loaded)

    @cached_property
    def entry_points(self) -> importlib_metadata.EntryPoints:
        """The entry points discovered for the given *group*."""
        if self._group is None:
            return importlib_metadata.EntryPoints()
        return importlib_metadata.entry_points(group=self._group)

    @cached_property
    def _unloaded_plugins(self) -> dict[str, importlib_metadata.EntryPoints]:
        """Note that this is a cached, mutable property.

        We initialize it once and then keep modifying the same instance.
        """
        entry_points = self.entry_points
        return {name: entry_points.select(name=name) for name in entry_points.names}


def _load_plugin(plugin: importlib_metadata.EntryPoint, /) -> None:
    """Load the entry point and call it if necessary.

    This expects the `EnvRegistry.namespace()` to be set up by the
    caller.
    """
    # Local import to prevent circular dependencies.
    from .._typeguards import is_problem_class

    possibly_fn = plugin.load()
    if plugin.attr and not is_problem_class(possibly_fn):
        if callable(possibly_fn):
            possibly_fn()
        else:
            raise TypeError("entry point is neither module nor callable")
