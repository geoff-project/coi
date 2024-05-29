# SPDX-FileCopyrightText: 2020-2024 CERN
# SPDX-FileCopyrightText: 2023-2024 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

# pylint: disable = import-outside-toplevel
# pylint: disable = invalid-name
# pylint: disable = redefined-builtin
# pylint: disable = too-many-arguments
# pylint: disable = unused-argument

"""Configuration file for the Sphinx documentation builder.

This file only contains a selection of the most common options. For a
full list see the documentation:
https://www.sphinx-doc.org/en/master/usage/configuration.html
"""

# -- Path setup --------------------------------------------------------

from __future__ import annotations

import enum
import importlib
import inspect
import pathlib
import typing as t

from sphinx.ext import intersphinx

try:
    import importlib_metadata
except ImportError:
    # Starting with Python 3.10 (see pyproject.toml).
    # pylint: disable = ungrouped-imports
    import importlib.metadata as importlib_metadata  # type: ignore[import, no-redef]

if t.TYPE_CHECKING:
    # pylint: disable = unused-import
    from docutils import nodes
    from sphinx import addnodes
    from sphinx.application import Sphinx
    from sphinx.environment import BuildEnvironment

ROOTDIR = pathlib.Path(__file__).absolute().parent.parent


# -- Project information -----------------------------------------------

project = "cernml-coi"
copyright = "2020–2024 CERN, 2023–2024 GSI Helmholtzzentrum für Schwerionenforschung"  # noqa: RUF001
author = "Nico Madysa"

release = importlib_metadata.version("cernml-coi")


# -- General configuration ---------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosectionlabel",
    "sphinx.ext.graphviz",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "sphinx_inline_tabs",
]

# Add any paths that contain templates here, relative to this directory.
# templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = [
    ".DS_Store",
    "Thumbs.db",
    "_build",
]

# Don't repeat the class name for methods and attributes in the page
# table of content of class API docs.
toc_object_entries_show_parents = "hide"

# Avoid role annotations as much as possible.
default_role = "py:obj"

# -- Options for Autodoc -----------------------------------------------

autodoc_member_order = "groupwise"
autodoc_typehints = "signature"
autodoc_type_aliases = {
    "ConfigValues": "~cernml.coi.ConfigValues",
}

napoleon_google_docstring = True
napoleon_numpy_docstring = False

# -- Options for Graphviz ----------------------------------------------

graphviz_output_format = "svg"

# -- Options for Intersphinx -------------------------------------------


def acc_py_docs_link(repo: str) -> str:
    """A URL pointing to the Acc-Py docs server."""
    return f"https://acc-py.web.cern.ch/gitlab/{repo}/docs/stable/"


def rtd_link(name: str, branch: str = "stable") -> str:
    """A URL pointing to a Read The Docs project."""
    return f"https://{name}.readthedocs.io/en/{branch}"


intersphinx_mapping = {
    "utils": (acc_py_docs_link("geoff/cernml-coi-utils"), None),
    "optimizers": (acc_py_docs_link("geoff/cernml-coi-optimizers"), None),
    "japc": (acc_py_docs_link("scripting-tools/pyjapc"), None),
    "mpl": ("https://matplotlib.org/stable/", None),
    "np": ("https://numpy.org/doc/stable/", None),
    "sci": ("https://docs.scipy.org/doc/scipy/reference/", None),
    "std": ("https://docs.python.org/3/", None),
    "pkg": ("https://packaging.python.org/en/latest/", None),
    "sb3": (rtd_link("stable-baselines3", branch="master"), None),
    "setuptools": (rtd_link("setuptools"), None),
    "importlib_metadata": (rtd_link("importlib-metadata"), None),
    "black": (rtd_link("black"), None),
}

# -- Options for HTML output -------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation
# for a list of builtin themes.
html_theme = "sphinxdoc"

# Add any paths that contain custom static files (such as style sheets)
# here, relative to this directory. They are copied after the builtin
# static files, so a file named "default.css" will overwrite the builtin
# "default.css". html_static_path = ["_static"]


# -- Custom code -------------------------------------------------------


def replace_modname(modname: str) -> None:
    """Change the module that a list of objects publicly belongs to.

    This package follows the pattern to have private modules called
    :samp:`_{name}` that expose a number of classes and functions that
    are meant for public use. The parent package then exposes these like
    this::

        from ._name import Thing

    However, these objects then still expose the private module via
    their ``__module__`` attribute::

        assert Thing.__module__ == 'parent._name'

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


# Do submodules first so that `coi.check()` is correctly assigned.
replace_modname("cernml.coi.checkers")
replace_modname("cernml.coi")


def retry_resolve_xref(
    app: Sphinx,
    env: BuildEnvironment,
    node: addnodes.pending_xref,
    contnode: nodes.TextElement,
) -> nodes.Element | None:
    """Run the resolve procedure again.

    This should be called after `node` has been modified in some way. It
    first tries the internal resolver before resorting to Intersphinx.
    """
    domain = env.domains[node["refdomain"]]
    return domain.resolve_xref(
        env,
        node["refdoc"],
        app.builder,
        node["reftype"],
        node["reftarget"],
        node,
        contnode,
    ) or intersphinx.missing_reference(app, env, node, contnode)


def fix_xrefs(
    app: Sphinx,
    env: BuildEnvironment,
    node: addnodes.pending_xref,
    contnode: nodes.TextElement,
) -> nodes.Element | None:
    """Link type variables to `typing.TypeVar`."""
    target = node["reftarget"]
    if target in ("T", ".T"):
        # Link type variables to typing.TypeVar.
        node["reftarget"] = "typing.TypeVar"
    elif hasattr(t, target):
        # Some typing members don't get their module resolved.
        node["reftarget"] = "typing." + target
    elif target.startswith("cernml.coi."):
        # Type aliases are `attr` or `data` but never `class`.
        node["reftype"] = "obj"
    return retry_resolve_xref(app, env, node, contnode)


def hide_enum_init_args(
    app: Sphinx,
    what: str,
    name: str,
    obj: object,
    options: dict[str, bool],
    signature: str,
    return_annotation: str,
) -> tuple[str, str] | None:
    """Hide all args to enum constructors except the first one."""
    if what == "class":
        assert isinstance(obj, type)
        if issubclass(obj, enum.Enum):
            # Extract all args and only keep the first.
            arg = signature.strip("()").split(", ", 1)[0]
            signature = f"({arg!s}: str)"
            return signature, return_annotation
    return None


def fix_generic_sigs(
    app: Sphinx,
    what: str,
    name: str,
    obj: object,
    options: dict[str, bool],
    signature: str,
    return_annotation: str,
) -> tuple[str, str] | None:
    """Fix generic function signatures generated by autodoc."""
    if signature and name.startswith("cernml.coi.Config") and "~.T" in signature:
        return signature.replace("~.T", "~T"), return_annotation
    return None


def setup(app: Sphinx) -> None:
    """Set up hooks into Sphinx."""
    app.connect("missing-reference", fix_xrefs)
    app.connect("autodoc-process-signature", hide_enum_init_args)
    app.connect("autodoc-process-signature", fix_generic_sigs)
