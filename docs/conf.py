"""Configuration file for the Sphinx documentation builder.

This file only contains a selection of the most common options. For a
full list see the documentation:
https://www.sphinx-doc.org/en/master/usage/configuration.html
"""

# pylint: disable = import-outside-toplevel
# pylint: disable = invalid-name
# pylint: disable = redefined-builtin

# -- Path setup --------------------------------------------------------

import datetime
import pathlib

ROOTDIR = pathlib.Path(__file__).absolute().parent.parent


def get_version() -> str:
    """Import the module and extract its version."""
    # Importing cernml.coi is fine – if we don't do it, the autodoc
    # extension does.
    import cernml.coi

    return cernml.coi.__version__


# -- Project information -----------------------------------------------

project = "cernml-coi"
copyright = f"{datetime.datetime.now().year}, BE-OP-SPS, CERN"
author = "Nico Madysa"

release = get_version()


# -- General configuration ---------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.graphviz",
    "sphinx.ext.intersphinx",
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

# -- Options for Autodoc -----------------------------------------------

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

# -- Options for Graphviz ----------------------------------------------

graphviz_output_format = "svg"

# -- Options for Intersphinx -------------------------------------------

ACC_PY_DOCS_ROOT = "https://acc-py.web.cern.ch/gitlab/"

intersphinx_mapping = {
    "utils": (
        ACC_PY_DOCS_ROOT + "be-op-ml-optimization/cernml-coi-utils/docs/stable/",
        None,
    ),
    "japc": (ACC_PY_DOCS_ROOT + "scripting-tools/pyjapc/docs/stable/", None),
    "mpl": ("https://matplotlib.org/stable/", None),
    "np": ("https://numpy.org/doc/stable/", None),
    "sci": ("https://docs.scipy.org/doc/scipy/reference/", None),
    "std": ("https://docs.python.org/3/", None),
    "setuptools": ("https://setuptools.readthedocs.io/en/latest/", None),
}

# -- Options for Myst-Parser -------------------------------------------

myst_enable_extensions = ["deflist"]
myst_heading_anchors = 3

# -- Options for HTML output -------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation
# for a list of builtin themes.
html_theme = "sphinxdoc"

# Add any paths that contain custom static files (such as style sheets)
# here, relative to this directory. They are copied after the builtin
# static files, so a file named "default.css" will overwrite the builtin
# "default.css". html_static_path = ["_static"]
