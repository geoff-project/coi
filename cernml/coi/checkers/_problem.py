"""Checker for the `Problem` ABC."""

import collections.abc
import inspect
import io
import typing as t
import warnings

import numpy as np

from .._machine import Machine
from .._problem import Problem

try:
    from matplotlib.figure import Figure
except ImportError:  # pragma: no cover
    MPL_AVAILABLE = False
else:
    MPL_AVAILABLE = True


def check_problem(
    problem: Problem, *, warn: bool = True, headless: bool = True
) -> None:
    """Check that a problem follows our conventions."""
    assert_machine(problem)
    assert_render_modes_defined(problem)
    assert_no_undeclared_render(problem, warn=warn, headless=headless)
    assert_execute_render(problem, headless=headless)
    if warn:
        warn_japc(problem)
        warn_cancellable(problem)
        warn_render_modes(problem)


def assert_machine(problem: Problem) -> None:
    """Check that the environment defines the machine it pertains to."""
    machine = problem.metadata.get("cern.machine")
    assert machine is not None, "missing key cern.machine in the environment metadata"
    assert isinstance(machine, Machine), "declared cern.machine is not a Machine enum"


def assert_render_modes_defined(problem: Problem) -> None:
    """Check that the environment defines render modes correctly."""
    # pylint: disable = unsubscriptable-object
    # pylint: disable = isinstance-second-argument-not-valid-type
    render_modes = t.cast(t.Collection[str], problem.metadata.get("render.modes"))
    assert (
        render_modes is not None
    ), "missing key render.modes in the environment metadata"
    # Circumvent <https://github.com/PyCQA/pylint/issues/3507>.
    assert isinstance(
        render_modes, collections.abc.Collection
    ), "render.modes must be a collection"
    for mode in render_modes:
        assert isinstance(mode, str), f"render mode must be string: {mode!r}"


def assert_no_undeclared_render(
    problem: Problem, *, warn: bool = True, headless: bool = True
) -> None:
    """Check for render modes that are implemented but not declared.

    Example:

        >>> from warnings import simplefilter
        >>> simplefilter("error")
        >>> class Foo(Problem):
        ...     def render(self, mode):
        ...         return None
        >>> assert_no_undeclared_render(Foo())
        Traceback (most recent call last):
        ...
        AssertionError: ... doesn't raise NotImplementedError
        >>> class Foo(Problem):
        ...     def render(self, mode):
        ...         raise TypeError()
        >>> assert_no_undeclared_render(Foo(), warn=False)
        >>> assert_no_undeclared_render(Foo())
        Traceback (most recent call last):
        ...
        UserWarning: ... raises instead: TypeError()
        >>> class Foo(Problem):
        ...     def render(self, mode):
        ...         return super().render(mode)
        >>> assert_no_undeclared_render(Foo())
    """
    # pylint: disable = broad-except
    # pylint: disable = unsubscriptable-object
    # pylint: disable = isinstance-second-argument-not-valid-type
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
    # pylint: disable = unsubscriptable-object
    # pylint: disable = isinstance-second-argument-not-valid-type

    def _assert_rgb_array(result: t.Any) -> None:
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

    def _assert_human(result: t.Any) -> None:
        assert result is None, f"render('rgb_array') should return None, not {result!r}"

    def _assert_ansi(result: t.Any) -> None:
        assert isinstance(
            result, (str, io.StringIO)
        ), f"render('ansi') should return str or StringIO, not {result!r}"

    def _assert_unmanaged_figure(figure: Figure) -> None:
        assert not hasattr(figure, "number"), (
            "figures returned by render('matplotlib_figures') "
            "must not be managed by PyPlot; create them via "
            "`matplotlib.figure.Figure()`"
        )

    def _assert_matplotlib_figures(result: t.Any) -> None:
        # Circumvent <https://github.com/PyCQA/pylint/issues/3507>.
        if isinstance(result, Figure):
            _assert_unmanaged_figure(result)
        elif hasattr(result, "items"):
            for title, figure in t.cast(dict, result):
                assert isinstance(title, str), f"not a string: {title!r}"
                assert isinstance(figure, Figure), f"not a figure: {figure}"
                _assert_unmanaged_figure(figure)
        elif hasattr(result, "__iter__") or hasattr(result, "__getitem__"):
            for item in t.cast(t.Iterable, result):
                if hasattr(item, "__iter__") or hasattr(item, "__getitem__"):
                    title, figure = t.cast(t.Tuple[t.Any, t.Any], item)
                    assert isinstance(title, str), f"not a string: {title!r}"
                    assert isinstance(figure, Figure), f"not a figure: {figure}"
                    _assert_unmanaged_figure(figure)
                else:
                    assert isinstance(item, Figure), f"not a figure: {item}"
                    _assert_unmanaged_figure(item)
        else:
            raise AssertionError(
                f"render('matplotlib_figures') returns {result}, "
                "which is neither a figure, nor a dict str->figure, "
                "nor a collection of figures or str-figure tuples"
            )

    additional_checks = {
        "rgb_array": _assert_rgb_array,
        "human": _assert_human,
        "ansi": _assert_ansi,
    }
    # Don't fail on missing matplotlib.
    if MPL_AVAILABLE:
        additional_checks["matplotlib_figures"] = _assert_matplotlib_figures
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
    """Check that the environment defines the required render modes.

    Example:

        >>> from warnings import simplefilter
        >>> simplefilter("error")
        >>> class Foo:
        ...     def __init__(self, modes):
        ...         self.metadata = {"render.modes": modes}
        >>> warn_render_modes(Foo([
        ...     "ansi", "human", "matplotlib_figures"
        ... ]))
        >>> warn_render_modes(Foo(["human", "matplotlib_figures"]))
        Traceback (most recent call last):
        ...
        UserWarning: missing render mode 'ansi': ...
        >>> warn_render_modes(Foo(["ansi", "matplotlib_figures"]))
        Traceback (most recent call last):
        ...
        UserWarning: missing render mode 'human': ...
        >>> warn_render_modes(Foo(["ansi", "human"]))
        Traceback (most recent call last):
        ...
        UserWarning: missing render mode 'matplotlib_figures': ...
    """
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


def warn_japc(problem: Problem) -> None:
    """Check that the environment declares JAPC usage.

    Example:

        >>> from warnings import simplefilter
        >>> simplefilter("error")
        >>> class Foo(Problem):
        ...     metadata = {}
        >>> warn_japc(Foo())
        Traceback (most recent call last):
        ...
        UserWarning: missing key 'cern.japc' ...
        >>> class Foo(Problem):
        ...     metadata = {"cern.japc": ""}
        >>> warn_japc(Foo())
        Traceback (most recent call last):
        ...
        UserWarning: ... should be a bool
        >>> class Foo(Problem):
        ...     metadata = {"cern.japc": True}
        >>> warn_japc(Foo())
        Traceback (most recent call last):
        ...
        UserWarning: ... accept a keyword argument ...
        >>> class Foo(Problem):
        ...     metadata = {"cern.japc": True}
        ...     def __init__(self, japc=None): pass
        >>> warn_japc(Foo())
    """
    _warn_flag_to_enable_init_arg(problem, "cern.japc", "japc")


def warn_cancellable(problem: Problem) -> None:
    """Check that the environment declares its cancellation policy."""
    _warn_flag_to_enable_init_arg(problem, "cern.cancellable", "cancellation_token")


def _warn_flag_to_enable_init_arg(
    problem: Problem, flag_name: str, arg_name: str
) -> None:
    """Check a flag that lets a user opt into an __init__ argument."""
    flag = problem.metadata.get(flag_name)
    if flag is None:
        return warnings.warn(
            f"missing key {flag_name!r} in the environment "
            "metadata; assuming the default value (False)"
        )
    if flag not in (True, False):
        return warnings.warn(f"declared {flag_name} should be a bool")
    if flag:
        init_signature = inspect.signature(type(problem.unwrapped).__init__)
        if arg_name not in init_signature.parameters:
            return warnings.warn(
                f"environments that declare {flag_name}=True should "
                f"accept a keyword argument {arg_name!r} in __init__()"
            )
    return None


def _get_blocked_modes(*, headless: bool = True) -> t.Sequence[str]:
    """Return a list of render modes that should _not_ be executed."""
    return ("human",) if headless else ()
