# SPDX-FileCopyrightText: 2020-2024 CERN
# SPDX-FileCopyrightText: 2023-2024 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

# pylint: disable = missing-function-docstring

"""Configuration file for the Sphinx documentation builder.

This file only contains a selection of the most common options. For a
full list see the documentation:
https://www.sphinx-doc.org/en/master/usage/configuration.html
"""

# -- Path setup --------------------------------------------------------

from __future__ import annotations

import pathlib
import sys
from pathlib import Path

try:
    import importlib_metadata
except ImportError:
    # Starting with Python 3.10 (see pyproject.toml).
    # pylint: disable = ungrouped-imports
    import importlib.metadata as importlib_metadata  # type: ignore[import, no-redef]


ROOTDIR = pathlib.Path(__file__).absolute().parent.parent


# -- Project information -----------------------------------------------

project = "cernml-coi"
dist = importlib_metadata.distribution(project)

copyright = "2020–2024 CERN, 2023–2024 GSI Helmholtzzentrum für Schwerionenforschung"
author = "Nico Madysa"
release = dist.version
version = release.partition("+")[0]

for entry in dist.metadata.get_all("Project-URL", []):
    url: str
    kind, url = entry.split(", ")
    if kind == "gitlab":
        gitlab_url = url.removesuffix("/")
        license_url = f"{gitlab_url}/-/blob/master/COPYING"
        issues_url = f"{gitlab_url}/-/issues"
        break
else:
    gitlab_url = ""
    license_url = ""
    issues_url = ""

# -- General configuration ---------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
sys.path.append(str(Path("./_ext").resolve()))
extensions = [
    "fix_napoleon_attributes_type",
    "fix_xrefs",
    "fixsig",
    "extra_directives",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosectionlabel",
    "sphinx.ext.graphviz",
    "sphinx.ext.inheritance_diagram",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "sphinx_inline_tabs",
]

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

# A list of prefixes that are ignored for sorting the Python module
# index.
modindex_common_prefix = ["cernml.", "cernml.coi.", "cernml.coi.registration."]

# Avoid role annotations as much as possible.
default_role = "py:obj"

# Use one line per argument for long signatures.
maximum_signature_line_length = 89

# -- Options for HTML output -------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation
# for a list of builtin themes.
html_theme = "python_docs_theme"
html_last_updated_fmt = "%b %d %Y"
html_theme_options = {
    "sidebarwidth": "21rem",
    "root_url": "https://acc-py.web.cern.ch/",
    "root_name": "Acc-Py Documentation server",
    "license_url": license_url,
    "issues_url": issues_url,
}
templates_path = ["./_templates/"]
html_static_path = ["./_static/"]

# -- Options for Autodoc -----------------------------------------------

autodoc_member_order = "bysource"
autodoc_typehints = "signature"
autodoc_default_options = {
    "members": True,
    "show-inheritance": True,
}
autodoc_type_aliases = {
    "ConfigValues": "~cernml.coi.ConfigValues",
    "InfoDict": "~cernml.coi.InfoDict",
}

napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_use_ivar = False
napoleon_attr_annotations = True

# -- Options for Graphviz ----------------------------------------------

graphviz_output_format = "svg"
graphviz_dot_args = ["-Tsvg:cairo"]

# -- Options for Autosectionlabel --------------------------------------

autosectionlabel_prefix_document = True
autosectionlabel_maxdepth = 3

# -- Options for Intersphinx -------------------------------------------


def acc_py_docs_link(repo: str) -> str:
    """A URL pointing to the Acc-Py docs server."""
    return f"https://acc-py.web.cern.ch/gitlab/{repo}/docs/stable"


def rtd_link(name: str, branch: str = "stable") -> str:
    """A URL pointing to a Read The Docs project."""
    return f"https://{name}.readthedocs.io/en/{branch}"


intersphinx_mapping = {
    "black": (rtd_link("black"), None),
    "gym": ("https://gymnasium.farama.org", None),
    "gymrob": ("https://robotics.farama.org", None),
    "importlib_metadata": (rtd_link("importlib-metadata"), None),
    "japc": (acc_py_docs_link("scripting-tools/pyjapc"), None),
    "mpl": ("https://matplotlib.org/stable", None),
    "np": ("https://numpy.org/doc/stable", None),
    "optimizers": (acc_py_docs_link("geoff/cernml-coi-optimizers"), None),
    "pkg": ("https://packaging.python.org/en/latest", None),
    "sb3": (rtd_link("stable-baselines3", branch="master"), None),
    "sci": ("https://docs.scipy.org/doc/scipy", None),
    "setuptools": ("https://setuptools.pypa.io/en/stable", None),
    "std": ("https://docs.python.org/3", None),
    "utils": (acc_py_docs_link("geoff/cernml-coi-utils"), None),
}


# -- Options for custom extension FixSig -------------------------------

fixsig_fix_dot_t = True
fixsig_hide_enum_init_args = True
fixsig_hide_exception_init_args = True
fixsig_hide_mcs_init_args = True

# -- Options for custom extension FixXrefs -----------------------------


fix_xrefs_try_typing = True
fix_xrefs_rules = [
    {
        "pattern": "(\\.T$|gymnasium.core.ObsType|gymnasium.core.ActType)",
        "reftarget": ("const", "typing.TypeVar"),
    },
    {
        "pattern": "^VectorEnv$",
        "reftarget": ("const", "gymnasium.experimental.vector.VectorEnv"),
    },
    {"pattern": "^Wrapper$", "reftarget": ("const", "gymnasium.Wrapper")},
    {"pattern": "^(ParamType|Constraint|AnyOptimizable)$"},
    {
        "pattern": "^_base\\.",
        "reftarget": ("sub", "gymnasium.envs.registration."),
        "contnode": ("sub", ""),
    },
    {"pattern": "^numpy.bool_"},
    {"pattern": "^numpy.typing.NDArray"},
    {"pattern": "^cernml\\.coi\\._goalenv\\.", "reftarget": ("sub", "cernml.coi.")},
    {"pattern": "^cernml\\.coi\\."},
    {"pattern": "^t\\.", "reftarget": ("sub", "typing."), "contnode": ("sub", "")},
]
