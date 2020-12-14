#!/usr/bin/env python

"""Package of various tools that make working with the COIs."""

try:
    from ._render import iter_matplotlib_figures
except ImportError:
    # Optional dependency: No error if matplotlib is missing.
    pass
