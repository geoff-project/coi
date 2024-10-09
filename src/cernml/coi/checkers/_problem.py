# SPDX-FileCopyrightText: 2020 - 2024 CERN
# SPDX-FileCopyrightText: 2023 - 2024 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

"""Checker for the `Problem` ABC."""

import collections.abc
import inspect
import typing as t
import warnings

import gymnasium

from .._machine import Machine
from .._typeguards import is_problem
from ..protocols import Problem
from ._generic import bump_warn_arg
from ._render import get_render_mode_checks


def check_problem(problem: Problem, *, warn: int = True, headless: bool = True) -> None:
    """Check the run-time invariants of the given interface."""
    warn = bump_warn_arg(warn)
    assert is_problem(problem), f"doesn't implement the Problem API: {problem!r}"
    assert_machine(problem)
    assert_render_modes_defined(problem)
    assert_render_mode_valid(problem, warn=warn)
    assert_execute_render(problem, headless=headless)
    if warn:
        warn_deprecated_attrs(problem, warn)
        warn_japc(problem, warn)
        warn_cancellable(problem, warn)
        warn_render_modes(problem, warn)


def assert_machine(problem: Problem) -> None:
    """Check that the environment defines the machine it pertains to."""
    machine = problem.metadata.get("cern.machine")
    assert machine is not None, "missing key cern.machine in the environment metadata"
    assert isinstance(machine, Machine), "declared cern.machine is not a Machine enum"


def assert_render_modes_defined(problem: Problem) -> None:
    """Check that the environment defines render modes correctly."""
    assert (
        "render.modes" not in problem.metadata
    ), "The metadata key `render.modes` is deprecated; use `render_modes` instead"
    render_modes = t.cast(t.Collection[str], problem.metadata.get("render_modes"))
    assert (
        render_modes is not None
    ), "missing key render_modes in the environment metadata"
    # Circumvent <https://github.com/PyCQA/pylint/issues/3507>.
    assert isinstance(
        render_modes, collections.abc.Collection
    ), "render_modes must be a collection"
    for mode in render_modes:
        assert isinstance(mode, str), f"render mode must be string: {mode!r}"


def assert_render_mode_valid(problem: Problem, *, warn: int = True) -> None:
    """Check whether the current render mode is a valid one.

    Example:

        >>> from warnings import simplefilter
        >>> simplefilter("error")
        >>> class Foo:
        ...     metadata = {"render.modes": []}
        ...     def __init__(self, render_mode=None):
        ...         self.render_mode = render_mode
        >>> assert_render_mode_valid(Foo())
        Traceback (most recent call last):
        ...
        UserWarning: ...`render.modes` is deprecated...

        >>> class Foo:
        ...     metadata = {}
        ...     def __init__(self, render_mode=None):
        ...         self.render_mode = render_mode
        >>> assert_render_mode_valid(Foo())
        >>> assert_render_mode_valid(Foo(render_mode="human"))
        Traceback (most recent call last):
        ...
        AssertionError: ...uses render mode 'human', which is not
        among the declared render modes: []

        >>> from cernml.coi import Problem
        >>> class Foo(Problem):
        ...     metadata = {"render_modes": ["human"]}
        >>> assert_render_mode_valid(Foo(render_mode="human"))
    """
    render_modes = problem.metadata.get("render.modes", None)
    if warn and render_modes is not None:
        warnings.warn(
            "The metadata key `render.modes` is deprecated; "
            "use `render_modes` instead",
            stacklevel=max(2, warn),
        )
    render_modes = problem.metadata.get("render_modes", render_modes or ())
    render_mode = problem.render_mode
    assert render_mode is None or render_mode in render_modes, (
        f"env uses render mode {render_mode!r}, which is not among "
        f"the declared render modes: {list(render_modes)!r}"
    )


def assert_execute_render(
    problem: Problem, *, warn: int = True, headless: bool = True
) -> None:
    """Check that current render mode can be executed.

    Example:

        >>> from cernml.coi import Problem
        >>> from warnings import simplefilter
        >>> simplefilter("error")
        >>> class Foo(Problem):
        ...     metadata = {"render_modes": ["human"]}
        >>> assert_execute_render(Foo(render_mode="human"))
        Traceback (most recent call last):
        ...
        UserWarning: ...cannot be run while headless=True

        >>> class Foo(Problem):
        ...     metadata = {"render_modes": ["ansi"]}
        >>> assert_execute_render(Foo(render_mode="ansi"))
        Traceback (most recent call last):
        ...
        AssertionError: render mode 'ansi' declared ...

        >>> class Foo(Problem):
        ...     metadata = {"render_modes": ["ansi", "custom"]}
        ...     def __init__(self, render_mode=None):
        ...         self.render_mode = render_mode
        ...     def render(self):
        ...         return None
        >>> assert_execute_render(Foo(render_mode="ansi"))
        Traceback (most recent call last):
        ...
        AssertionError: ...should return str or StringIO, not None
        >>> assert_execute_render(Foo(render_mode="custom"))
    """
    additional_checks = get_render_mode_checks()
    blocked_modes = _get_blocked_modes(headless=headless)
    mode = problem.render_mode
    if mode is None:
        return
    if mode in blocked_modes:
        warnings.warn(
            f"render mode is set to {mode!r}, which cannot be run "
            f"while headless={headless!r}",
            stacklevel=max(2, warn),
        )
        # Not necessary to cover this line as long as we cover the
        # warning above.
        return  # pragma: no cover
    try:
        result = problem.render()
    except NotImplementedError as exc:
        raise AssertionError(
            f"render mode {mode!r} declared but not implemented"
        ) from exc
    if additional_check := additional_checks.get(mode):
        additional_check(result)


def warn_deprecated_attrs(problem: Problem, warn: int = True) -> None:
    """Check that the problem doesn't define deprecated attributes.

    Example:

        >>> from warnings import simplefilter
        >>> simplefilter("error")
        >>> class Foo(Problem):
        ...     reward_range = (0.0, 1.0)
        >>> warn_deprecated_attrs(Foo())
        Traceback (most recent call last):
        ...
        UserWarning: attribute 'reward_range' is deprecated, ...
        >>> class Bar(Problem):
        ...     objective_range = (0.0, 1.0)
        >>> warn_deprecated_attrs(Bar())
        Traceback (most recent call last):
        ...
        UserWarning: attribute 'objective_range' is deprecated, ...
        >>> class Baz(Problem):
        ...     pass
        >>> warn_deprecated_attrs(Baz())

        No spurious warnings when used with a Gymnasium wrapper:

        >>> from gymnasium import Env
        >>> from gymnasium.wrappers import TimeLimit
        ...
        >>> class Baz(Env):
        ...     pass
        ...
        >>> warn_deprecated_attrs(TimeLimit(Baz(), 10))
    """
    for attr in ("objective_range", "reward_range"):
        try:
            value = problem.get_wrapper_attr(attr)
        except AttributeError:
            continue
        if value is not None and value is not getattr(gymnasium.Env, attr, None):
            warnings.warn(
                f"attribute {attr!r} is deprecated, you should not define it anymore",
                stacklevel=max(2, warn),
            )


def warn_render_modes(problem: Problem, warn: int = True) -> None:
    """Check that the environment defines the required render modes.

    Example:

        >>> from warnings import simplefilter
        >>> simplefilter("error")
        >>> class Foo:
        ...     def __init__(self, modes):
        ...         self.metadata = {"render_modes": modes}
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
    render_modes = t.cast(t.Collection[str], problem.metadata["render_modes"])
    if "ansi" not in render_modes:
        warnings.warn(
            "missing render mode 'ansi': This is the most basic "
            "render mode. In this mode, render() should return a "
            "`str` or `StringIO` for terminal output. The text may "
            "include newlines and ANSI escape sequences (e.g. for "
            "colors).",
            stacklevel=max(2, warn),
        )
    if "human" not in render_modes:
        warnings.warn(
            "missing render mode 'human': This is the ideal render "
            "mode for interactive use. In this mode, render() should "
            "print or plot the environment to the current display "
            "and return nothing. This mode is seldom used by other "
            "libraries.",
            stacklevel=max(2, warn),
        )
    if "matplotlib_figures" not in render_modes:
        warnings.warn(
            "missing render mode 'matplotlib_figures': This is a "
            "custom render mode used by the reference GUI. It is "
            "meant for embedding a generic problem into a Qt-based "
            "GUI. In this mode, render() should return a list of "
            "`matplotlib.figure.Figure()` objects, but not display "
            "in any way. This will be handled by the GUI instead.",
            stacklevel=max(2, warn),
        )


def warn_japc(problem: Problem, warn: int = True) -> None:
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
    _warn_flag_to_enable_init_arg(
        problem, flag_name="cern.japc", arg_name="japc", warn=bump_warn_arg(warn)
    )


def warn_cancellable(problem: Problem, warn: int = True) -> None:
    """Check that the environment declares its cancellation policy."""
    _warn_flag_to_enable_init_arg(
        problem,
        flag_name="cern.cancellable",
        arg_name="cancellation_token",
        warn=bump_warn_arg(warn),
    )


def _warn_flag_to_enable_init_arg(
    problem: Problem, flag_name: str, arg_name: str, warn: int = True
) -> None:
    """Check a flag that lets a user opt into an __init__ argument."""
    flag = problem.metadata.get(flag_name)
    if flag is None:
        return warnings.warn(
            f"missing key {flag_name!r} in the environment "
            "metadata; assuming the default value (False)",
            stacklevel=max(2, warn),
        )
    if flag not in (True, False):
        return warnings.warn(
            f"declared {flag_name} should be a bool",
            stacklevel=max(2, warn),
        )
    if flag:
        init_signature = inspect.signature(type(problem.unwrapped).__init__)
        if arg_name not in init_signature.parameters:
            return warnings.warn(
                f"environments that declare {flag_name}=True should "
                f"accept a keyword argument {arg_name!r} in __init__()",
                stacklevel=max(2, warn),
            )
    return None


def _get_blocked_modes(*, headless: bool = True) -> t.Sequence[str]:
    """Return a list of render modes that should *not* be executed."""
    return ("human",) if headless else ()
