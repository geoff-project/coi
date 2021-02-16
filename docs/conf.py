"""Configuration file for the Sphinx documentation builder.

This file only contains a selection of the most common options. For a full
list see the documentation:
https://www.sphinx-doc.org/en/master/usage/configuration.html
"""

# pylint: disable = import-outside-toplevel
# pylint: disable = invalid-name
# pylint: disable = redefined-builtin

# -- Path setup --------------------------------------------------------------

import datetime
import pathlib
import sys

import sphinx.application
from recommonmark.transform import AutoStructify

ROOTDIR = pathlib.Path(__file__).absolute().parent.parent

# TODO: Remove this, build docs from what we installed. This guarantees
# that setuptools-scm doesn't change the version number due to build
# artifacts.
# sys.path.insert(0, str(ROOTDIR))


def get_version() -> str:
    """Import the module and extract its version."""
    # Importing cernml.coi is fine – if we don't do it, the autodoc
    # extension does.
    import cernml.coi

    return cernml.coi.__version__


# -- Project information -----------------------------------------------------

project = "cernml-coi"
copyright = f"{datetime.datetime.now().year}, BE-OP-SPS, CERN"
author = "Nico Madysa"

release = get_version()


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "recommonmark",
    "sphinx.ext.autodoc",
    "sphinx.ext.graphviz",
    "sphinx.ext.napoleon",
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

# -- Options for Autodoc -----------------------------------------------------

autodoc_member_order = "groupwise"
autodoc_typehints = "signature"
autodoc_type_aliases = {
    "MatplotlibFigures": "cernml.coi.mpl_utils.MatplotlibFigures",
    "MaybeTitledFigure": "cernml.coi.mpl_utils.MaybeTitledFigure",
}

napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_type_aliases = {
    "Problem": "cernml.coi._problem.Problem",
}

# -- Options for Graphviz ----------------------------------------------------

graphviz_output_format = "svg"

# -- Options for Recommonmark ------------------------------------------------


def setup(app: sphinx.application.Sphinx) -> None:
    """Configure Recommonmark."""
    app.add_config_value(
        "recommonmark_config",
        {
            "auto_toc_tree_section": "Contents",
            "enable_eval_rst": True,
        },
        True,
    )
    app.add_transform(AutoStructify)


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
html_theme = "sphinx_rtd_theme"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
# html_static_path = ["_static"]
