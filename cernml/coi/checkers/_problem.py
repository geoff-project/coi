#!/usr/bin/env python

"""Checker for the `Problem` ABC."""

import io
import typing as t
import warnings

import numpy as np
from matplotlib.figure import Figure

from .._machine import Machine
from .._problem import Problem
from ..utils import iter_matplotlib_figures


def check_problem(
    problem: Problem, *, warn: bool = True, headless: bool = True
) -> None:
    """Check that a problem follows our conventions."""
    assert_machine(problem)
    assert_no_undeclared_render(problem, warn=warn, headless=headless)
    assert_execute_render(problem, headless=headless)
    if warn:
        warn_render_modes(problem)


def assert_machine(env: Problem) -> None:
    """Check that the environment defines the machine it pertains to."""
    machine = env.metadata.get("cern.machine")
    assert machine is not None, "missing key cern.machine in the environment metadata"
    assert isinstance(machine, Machine), "declared cern.machine is not a Machine enum"


def assert_render_modes(problem: Problem) -> None:
    """Check that the environment defines render modes correctly."""
    # pylint: disable = unsubscriptable-object
    render_modes = t.cast(t.Collection[str], problem.metadata.get("render.modes"))
    assert (
        render_modes is not None
    ), "missing key render.modes in the environment metadata"
    assert isinstance(render_modes, t.Collection), "render.modes must be a collection"
    for mode in render_modes:
        assert isinstance(mode, str), f"render mode must be string: {mode!r}"


def assert_no_undeclared_render(
    problem: Problem, *, warn: bool = True, headless: bool = True
) -> None:
    """Check for render modes that are implemented but not declared."""
    # pylint: disable = broad-except
    # pylint: disable = unsubscriptable-object
    blocked_modes = set(_get_blocked_modes(headless=headless))
    render_modes = set(t.cast(t.Collection[str], problem.metadata["render.modes"]))
    known_modes = {"ansi", "human", "matplotlib_figures", "rgb_array"}
    modes_to_check = known_modes - blocked_modes - render_modes
    for mode in modes_to_check:
        try:
            problem.render(mode)
        except (NotImplementedError, ValueError):
            pass
        except Exception as exc:
            if warn:
                warnings.warn(
                    f"calling render({mode!r}) should raise "
                    f"NotImplementedError or ValueError, but raises "
                    f"instead: {exc!r}"
                )
        else:
            raise AssertionError(
                f"calling render({mode!r}) with undeclared render "
                f"mode doesn't raise NotImplementedError"
            )


def assert_execute_render(problem: Problem, *, headless: bool = True) -> None:
    """Check that each declared render mode can be executed."""

    def _assert_rgb_array(result: t.Any) -> None:
        assert isinstance(
            result, np.ndarray
        ), f"render('rgb_array') should return a NumPy array, not {result!r}"
        num_dims = np.ndim(result)
        assert num_dims == 3, f"render('rgb_array') array should be 3D, not {num_dims}D"
        num_colors = np.shape(result)[-1]
        assert (
            num_colors == 3
        ), f"render('rgb_array') array should have shape (x, y, 3), not (x, y, {num_colors})"

    def _assert_human(result: t.Any) -> None:
        assert result is None, f"render('rgb_array') should return None, not {result!r}"

    def _assert_ansi(result: t.Any) -> None:
        assert isinstance(
            result, (str, io.StringIO)
        ), f"render('ansi') should return str or StringIO, not {result!r}"

    def _assert_matplotlib_figures(result: t.Any) -> None:
        assert isinstance(
            result, t.Collection
        ), f"render('matplotlib_figures') should return a collection, not {result!r}"
        for title, figure in iter_matplotlib_figures(result):
            assert isinstance(title, str), f"not a string: {title!r}"
            assert isinstance(figure, Figure), f"not a figure: {figure}"
            assert not hasattr(figure, "number"), (
                "figures returned by render('matplotlib_figures') "
                "must not be managed by PyPlot; create them via "
                "`matplotlib.figure.Figure()`"
            )

    # pylint: disable = unsubscriptable-object
    additional_checks = {
        "rgb_array": _assert_rgb_array,
        "human": _assert_human,
        "ansi": _assert_ansi,
        "matplotlib_figures": _assert_matplotlib_figures,
    }
    blocked_modes = _get_blocked_modes(headless=headless)
    render_modes = t.cast(t.Collection[str], problem.metadata["render.modes"])
    for mode in render_modes:
        if mode in blocked_modes:
            continue
        try:
            result = problem.render(mode)
        except NotImplementedError as exc:
            raise AssertionError(
                f"render mode {mode!r} declared but not implemented"
            ) from exc
        additional_check = additional_checks.get(mode)
        if additional_check:
            additional_check(result)


def warn_render_modes(problem: Problem) -> None:
    """Check that the environment defines the required render modes."""
    # pylint: disable = unsubscriptable-object
    render_modes = t.cast(t.Collection[str], problem.metadata["render.modes"])
    if "ansi" not in render_modes:
        warnings.warn(
            "missing render mode 'ansi': This is the most basic "
            "render mode. In this mode, render() should return a "
            "`str` or `StringIO` for terminal output. The text may "
            "include newlines and ANSI escape sequences (e.g. for "
            "colors)."
        )
    if "human" not in render_modes:
        warnings.warn(
            "missing render mode 'human': This is the ideal render "
            "mode for interactive use. In this mode, render() should "
            "print or plot the environment to the current display "
            "and return nothing. This mode is seldom used by other "
            "libraries."
        )
    if "matplotlib_figures" not in render_modes:
        warnings.warn(
            "missing render mode 'matplotlib_figures': This is a "
            "custom render mode used by acc-app-optimisation. It is "
            "meant for embedding a generic problem into a Qt-based "
            "GUI. In this mode, render() should return a list of "
            "`matplotlib.figure.Figure()` objects, but not display "
            "in any way. This will be handled by the GUI instead."
        )


def _get_blocked_modes(*, headless: bool = True) -> t.Sequence[str]:
    """Return a list of render modes that should _not_ be executed."""
    return ("human",) if headless else ()
