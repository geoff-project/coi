# SPDX-FileCopyrightText: 2020 - 2025 CERN
# SPDX-FileCopyrightText: 2023 - 2025 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

"""Provide the main entry point check()."""

import functools
import logging
import sys
import typing as t

import gymnasium as gym

from ._configurable import Configurable, check_configurable
from ._env import check_env
from ._func_opt import FunctionOptimizable, check_function_optimizable
from ._generic import bump_warn_arg
from ._problem import Problem, check_problem
from ._single_opt import SingleOptimizable, check_single_optimizable

if sys.version_info < (3, 10):
    import importlib_metadata
else:
    import importlib.metadata as importlib_metadata

LOG = logging.getLogger(__name__)


def check(env: Problem, warn: int = True, headless: bool = True) -> None:
    """Check that a problem follows the API of this package.

    Args:
        env: The object whose API is to be checked. Must at least be a
            `Problem`. If it satisfies other interfaces, like
            `SingleOptimizable` or `~gymnasium.Env`, all of their APIs
            are checked as well.
        headless: If True (the default), do not run tests that require a
            GUI.
        warn: If True (the default), run additional tests that might be
            indicative of problems but might also exhibit false
            positives. if False, no warnings are given.

    Raises:
        AssertionError: if any check fails.

    .. note::
        The *warn* parameter is actually an integer. If it's nonzero,
        :samp:`max(2, {warn})` is used to calculate the *stacklevel*
        passed to :func:`~warnings.warn()`. Higher values push the
        reported offending location further up the stack trace. This
        allows you to attribute a warning to the correct optimization
        problem even when calling this function from a wrapper.
    """
    unwrapped_env = getattr(env, "unwrapped", None)
    assert unwrapped_env is not None, f'missing property "unwrapped" on {type(env)}'
    assert isinstance(unwrapped_env, Problem), (
        f"{type(unwrapped_env)} must inherit from Problem"
    )
    # Run built-in checkers.
    warn = bump_warn_arg(warn)
    LOG.debug("Checking Problem interface of %s", env)
    check_problem(env, warn=warn, headless=headless)
    if isinstance(unwrapped_env, SingleOptimizable):
        LOG.debug("Checking SingleOptimizable interface of %s", env)
        check_single_optimizable(t.cast(SingleOptimizable, env), warn=warn)
    if isinstance(unwrapped_env, FunctionOptimizable):
        LOG.debug("Checking FunctionOptimizable interface of %s", env)
        check_function_optimizable(t.cast(FunctionOptimizable, env), warn=warn)
    if isinstance(unwrapped_env, gym.Env):
        LOG.debug("Checking Env interface of %s", env)
        check_env(t.cast(gym.Env, env), warn=warn)
    if isinstance(unwrapped_env, Configurable):
        LOG.debug("Checking Configurable interface of %s", env)
        check_configurable(t.cast(Configurable, env), warn=warn)
    # Run plug-in checkers.
    for name, checker in load_extra_checkers():
        LOG.debug("Running checker plugin %r on %s", name, env)
        checker(env, warn=warn, headless=headless)


class Checker(t.Protocol):
    """Expected signature of checker plugins."""

    def __call__(
        self, problem: Problem, *, warn: int = True, headless: bool = True
    ) -> None:
        raise NotImplementedError


@functools.cache
def load_extra_checkers(
    group: str = "cernml.checkers",
) -> t.Sequence[tuple[str, Checker]]:
    """Load all checker plugins.

    Args:
        group: The entry point group to load.

    Returns:
        A sequence of tuples :samp:`({entry point name}, {loaded
        checker})`. Faulty plugins are logged, but otherwise excluded
        from the list.

        The return value is cached, so you can call this function as
        often as you want.
    """
    checkers = []
    entry_points = importlib_metadata.entry_points().select(group=group)
    for entry_point in entry_points:
        name = entry_point.name
        LOG.debug("Loading checker plugin: %s", name)
        try:
            checker: Checker = entry_point.load()
        except Exception:
            LOG.exception("ignored plugin %r: loading raised an exception", name)
            continue
        if not callable(checker):
            LOG.error("ignored plugin %r: %r is not callable", name, checker)
            continue
        checkers.append((name, checker))
    return tuple(checkers)
