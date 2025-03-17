# SPDX-FileCopyrightText: 2020 - 2024 CERN
# SPDX-FileCopyrightText: 2023 - 2024 GSI Helmholtzzentrum für Schwerionenforschung
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


def get_render_mode_checks() -> dict[str, t.Callable[..., None]]:
    """Return a mapping from render mode to checker for that mode."""
    checks = {
        "rgb_array_list": assert_rgb_array_list,
        "rgb_array": assert_rgb_array,
        "human": assert_human,
        "ansi_list": assert_ansi_list,
        "ansi": assert_ansi,
    }
    # Don't fail on missing matplotlib.
    if MPL_AVAILABLE:
        checks["matplotlib_figures"] = assert_matplotlib_figures
    return checks


def assert_rgb_array_list(result: t.Any) -> None:
    """Assert that *result* is a list of RGB images.

    Example:

        >>> image = np.zeros((36, 36, 3))
        >>> assert_rgb_array_list([image, image])
        >>> assert_rgb_array_list([image, image, None, image])
        Traceback (most recent call last):
        ...
        AssertionError: item #2 of the render('rgb_array_list')
        result is invalid, see the exception above
    """
    assert is_iterable(
        result
    ), "render('rgb_array_list') should return a list of NumPy arrays, not {result!r}"
    try:
        for i, image in enumerate(result):  # noqa: B007
            assert_rgb_array(image)
    except AssertionError as exc:
        raise AssertionError(
            f"item #{i} of the render('rgb_array_list') result is "
            f"invalid, see the exception above"
        ) from exc


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


def assert_ansi_list(result: t.Any) -> None:
    """Assert that *result* is a list of strings or StringIO.

    Example:

        >>> assert_ansi_list(list("abcde"))
        >>> assert_ansi_list(["1", "2", 3, "4"])
        Traceback (most recent call last):
        ...
        AssertionError: image #2 of the render('rgb_array_list')
        result is invalid, see the exception above
    """
    assert is_iterable(
        result
    ), "render('ansi_list') should return a list of strings, not {result!r}"
    try:
        for i, string in enumerate(result):  # noqa: B007
            assert_ansi(string)
    except AssertionError as exc:
        raise AssertionError(
            f"item #{i} of the render('ansi_list') result is "
            f"invalid, see the exception above"
        ) from exc


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
        >>> assert_matplotlib_figures([("foo", Figure())])
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
    assert getattr(figure, "number", None) is None, (
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
            t.cast(tuple[t.Any, t.Any], item) if is_iterable(item) else ("", item)
        )
        _assert_mpl_figures_item(title, figure)


def _assert_mpl_figures_item(title: t.Any, figure: t.Any) -> None:
    assert isinstance(title, str), f"not a string: {title!r}"
    assert isinstance(figure, Figure), f"not a figure: {figure}"
    assert_unmanaged_figure(figure)
