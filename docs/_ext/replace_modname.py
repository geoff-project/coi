# SPDX-FileCopyrightText: 2020-2024 CERN
# SPDX-FileCopyrightText: 2023-2024 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

"""Change the module that a list of objects publicly belongs to.

Some packages follow the pattern to have private modules called
:samp:`_{name}` that expose a number of classes and functions that
are meant for public use. The parent package then exposes these like
this::

    from ._name import Thing

However, these objects then still expose the private module via
their ``__module__`` attribute::

    assert Thing.__module__ == 'parent._name'

This extension defines a config option ``replace_modnames`` that is
a list of strings. Each string must be a package name, possibly nested.

For each package name, this extension imports the package, iterates
through all exported members (as determined by either ``__all__`` or
`vars()`) and fixes each one's module of origin up to be the name of the
package. It does so recursively for all public attributes (i.e. those
whose name does not have a leading underscore).
"""

from __future__ import annotations

import importlib
import inspect
import typing as t

if t.TYPE_CHECKING:
    from sphinx.application import Config, Sphinx
    from sphinx.util.typing import ExtensionMetadata


def pubnames(obj: object) -> t.Iterator[str]:
    """Return an iterator over the public names in an object."""
    return iter(
        t.cast(list[str], getattr(obj, "__all__", None))
        or (
            name
            for name, _ in inspect.getmembers_static(obj)
            if not name.startswith("_")
        )
    )


def _is_true_prefix(prefix: str, full: str) -> bool:
    return full.startswith(prefix) and full != prefix


def replace_modname(modname: str) -> None:
    """Change the module that a list of objects publicly belongs to.

    This function iterates through all exported members of the package
    or module *modname* (as determined by either ``__all__`` or
    `vars()`) and fixes each one's module of origin up to be the
    *modname*. It does so recursively for all public attributes (i.e.
    those whose name does not have a leading underscore).
    """
    todo: list[object] = [importlib.import_module(modname)]
    while todo:
        parent = todo.pop()
        for pubname in pubnames(parent):
            obj = inspect.getattr_static(parent, pubname)
            private_modname = getattr(obj, "__module__", "")
            if private_modname and _is_true_prefix(modname, private_modname):
                obj.__module__ = modname
                todo.append(obj)


def handle_config_inited(app: Sphinx, config: Config) -> None:
    """Replace all configured module names."""
    attr = getattr(config, "replace_modnames", ())
    if isinstance(attr, str):
        raise TypeError("config option 'replace_modnames' must be list of str, not str")
    modnames = list(attr)
    for modname in modnames:
        replace_modname(modname)


def setup(app: Sphinx) -> ExtensionMetadata:
    """Set up hooks into Sphinx."""
    app.add_config_value("replace_modnames", [], "html", list[str])
    app.connect("config-inited", handle_config_inited)
    return {
        "version": "1.0",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
