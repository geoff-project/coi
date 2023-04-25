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
import types

try:
    import importlib_metadata
except ImportError:
    # Starting with Python 3.10 (see pyproject.toml).
    import importlib.metadata as importlib_metadata  # type: ignore

ROOTDIR = pathlib.Path(__file__).absolute().parent.parent


# -- Project information -----------------------------------------------

project = "cernml-coi"
copyright = f"{datetime.datetime.now().year}, BE-OP-SPS, CERN"
author = "Nico Madysa"

release = importlib_metadata.version("cernml-coi")


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

napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_type_aliases = {
    "Problem": "cernml.coi._problem.Problem",
}


def setup(app):  # type: ignore
    """Sphinx setup hook."""

    def _deduce_public_module_name(name):  # type: ignore
        if name.startswith("cernml.coi._"):
            return "cernml.coi"
        if name == "gym.core":
            return "gym"
        if name.startswith("gym.spaces."):
            return "gym.spaces"
        return name

    def _hide_configurable_module(obj):  # type: ignore
        annotations = getattr(obj, "__annotations__", {})
        if annotations.get("return") == "Config":
            annotations["return"] = "cernml.coi.Config"

    def _hide_class_module(class_):  # type: ignore
        old_name = getattr(class_, "__module__", "")
        if not old_name:
            return
        new_name = _deduce_public_module_name(old_name)
        if new_name != old_name:
            class_.__module__ = new_name

    def _hide_checker_arg(func):  # type: ignore
        name = func.__name__
        if name != "check" and not name.startswith("check_"):
            return
        for type_ in func.__annotations__.values():
            _hide_class_module(type_)

    def _hide_return_value(func):  # type: ignore
        name = func.__name__
        if name.endswith("_space"):
            return_type = func.__annotations__.get("return")
            if return_type and isinstance(return_type, type):
                _hide_class_module(return_type)

    def _resolve_problem_string(func):  # type: ignore
        # Manually resolve this reference so that Sphinx does not insert
        # the hidden `_problem` module.
        return_type = func.__annotations__.get("return")
        if return_type and return_type == "Problem":
            func.__annotations__["return"] = "cernml.coi.Problem"

    def _hide_private_modules(_app, obj, _bound_method):  # type: ignore
        if isinstance(obj, type):
            if obj.__name__ == "Problem":
                _resolve_problem_string(obj.unwrapped.fget)
            for base in obj.__mro__:
                _hide_class_module(base)
            for attr_type in obj.__annotations__.values():
                if isinstance(obj, type):
                    _hide_class_module(attr_type)
        elif isinstance(obj, types.FunctionType):
            _hide_checker_arg(obj)
            _hide_return_value(obj)
        _hide_configurable_module(obj)

    app.connect("autodoc-before-process-signature", _hide_private_modules)


# -- Options for Graphviz ----------------------------------------------

graphviz_output_format = "svg"

# -- Options for Intersphinx -------------------------------------------

ACC_PY_DOCS_ROOT = "https://acc-py.web.cern.ch/gitlab/"
RTD_TEMPLATE = "https://{}.readthedocs.io/en/latest"

intersphinx_mapping = {
    "utils": (
        ACC_PY_DOCS_ROOT + "geoff/cernml-coi-utils/docs/stable/",
        None,
    ),
    "japc": (ACC_PY_DOCS_ROOT + "scripting-tools/pyjapc/docs/stable/", None),
    "mpl": ("https://matplotlib.org/stable/", None),
    "np": ("https://numpy.org/doc/stable/", None),
    "sci": ("https://docs.scipy.org/doc/scipy/reference/", None),
    "std": ("https://docs.python.org/3/", None),
    "setuptools": (RTD_TEMPLATE.format("setuptools"), None),
    "importlib_metadata": (RTD_TEMPLATE.format("importlib-metadata"), None),
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
