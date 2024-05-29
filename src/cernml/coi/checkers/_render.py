# SPDX-FileCopyrightText: 2020-2024 CERN
# SPDX-FileCopyrightText: 2023-2024 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

"""Helpers for checks of the render method."""

import io
import typing as t

import numpy as np

from ._generic import is_iterable

try:
    from matplotlib.figure import Figure
except ImportError:
    MPL_AVAILABLE = False
else:
    MPL_AVAILABLE = True


def get_render_mode_checks() -> t.Dict[str, t.Callable[..., None]]:
    """Return a mapping from render mode to checker for that mode."""
    # TODO: Add rgb_array_list and ansi_list; Handle new semantics of
    # `human` (render() call not necessary)
    checks = {
        "rgb_array": assert_rgb_array,
        "human": assert_human,
        "ansi": assert_ansi,
    }
    # Don't fail on missing matplotlib.
    if MPL_AVAILABLE:
        checks["matplotlib_figures"] = assert_matplotlib_figures
    return checks


def assert_rgb_array(result: t.Any) -> None:
    """Assert that *result* is an RGB image.

    Example:

        >>> assert_rgb_array(np.zeros((36, 36, 3)))
    """
    assert isinstance(
        result, np.ndarray
    ), f"render('rgb_array') should return a NumPy array, not {result!r}"
    num_dims = np.ndim(result)
    assert num_dims == 3, f"render('rgb_array') array should be 3D, not {num_dims}D"
    num_colors = np.shape(result)[-1]
    assert num_colors == 3, (
        f"render('rgb_array') array should have shape (x, y, 3), "
        f"not (x, y, {num_colors})"
    )


def assert_human(result: t.Any) -> None:
    """Assert that *result* maches the "human" render mode.

    Example:

        >>> assert_human(None)
    """
    assert result is None, f"render('human') should return None, not {result!r}"


def assert_ansi(result: t.Any) -> None:
    """Assert that *result* maches the "ansi" render mode.

    Example:

        >>> assert_ansi("")
    """
    assert isinstance(
        result, (str, io.StringIO)
    ), f"render('ansi') should return str or StringIO, not {result!r}"


def assert_matplotlib_figures(result: t.Any) -> None:
    """Assert that *result* matches the "matplotlib_figures" mode.

    Example:

        >>> assert_matplotlib_figures(Figure())
        >>> assert_matplotlib_figures({"foo": Figure()})
        >>> assert_matplotlib_figures("foo")
        Traceback (most recent call last):
        ...
        AssertionError: render('matplotlib_figures') returns ...
    """
    # Circumvent <https://github.com/PyCQA/pylint/issues/3507>.
    if isinstance(result, Figure):
        return assert_unmanaged_figure(result)
    if hasattr(result, "items"):
        return assert_mpl_figures_dict(t.cast(dict, result))
    if is_iterable(result) and not isinstance(result, str):
        return assert_mpl_figures_iterable(t.cast(t.Iterable, result))
    raise AssertionError(
        f"render('matplotlib_figures') returns {result}, "
        "which is neither a figure, nor a dict str->figure, "
        "nor a collection of figures or str-figure tuples"
    )


def assert_unmanaged_figure(figure: "Figure") -> None:
    """Assert that *figure* is not managed by PyPlot."""
    assert not hasattr(figure, "number"), (
        "figures returned by render('matplotlib_figures') "
        "must not be managed by PyPlot; create them via "
        "`matplotlib.figure.Figure()`"
    )


def assert_mpl_figures_dict(result: dict) -> None:
    """Assert that *result* maps from string to unmanaged figure."""
    for title, figure in t.cast(dict, result).items():
        _assert_mpl_figures_item(title, figure)


def assert_mpl_figures_iterable(result: t.Iterable) -> None:
    """Assert that *result* is an iterable of figures and titles."""
    for item in t.cast(t.Iterable, result):
        title, figure = (
            t.cast(t.Tuple[t.Any, t.Any], item) if is_iterable(item) else ("", item)
        )
        _assert_mpl_figures_item(title, figure)


def _assert_mpl_figures_item(title: t.Any, figure: t.Any) -> None:
    assert isinstance(title, str), f"not a string: {title!r}"
    assert isinstance(figure, Figure), f"not a figure: {figure}"
    assert_unmanaged_figure(figure)
