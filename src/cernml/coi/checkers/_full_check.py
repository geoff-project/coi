# SPDX-FileCopyrightText: 2020-2024 CERN
# SPDX-FileCopyrightText: 2023-2024 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

"""Provide the main entry point check()."""

import logging
import typing as t

import gymnasium as gym

try:
    import importlib_metadata
except ImportError:
    # Starting with Python 3.10 (see pyproject.toml).
    import importlib.metadata as importlib_metadata  # type: ignore[import, no-redef]

from ._configurable import Configurable, check_configurable
from ._env import check_env
from ._func_opt import FunctionOptimizable, check_function_optimizable
from ._generic import bump_warn_arg
from ._problem import Problem, check_problem
from ._single_opt import SingleOptimizable, check_single_optimizable

LOG = logging.getLogger(__name__)


def check(env: Problem, warn: int = True, headless: bool = True) -> None:
    """Check that a problem follows the API of this package.

    Args:
        env: The object whose API is to be checked. Must at least be a
            `Problem`. If it satisfies other interfaces, like
            `SingleOptimizable` or `~gym.Env`, all of their APIs are
            checked as well.
        headless: If True (the default), do not run tests that require a
            GUI.
        warn: If True (the default), run additional tests that might be
            indicative of problems but might also exhibit false
            positives. if False, no warnings are given.

    Raises:
        AssertionError: if any check fails.

    This method provides a plugin interface via the :ref:`entry point
    <setuptools:dynamic discovery of services and plugins>`
    ``"cernml.coi.checkers"``. This means that other packages may
    provide additional checkers. Upon each call, this method will load
    all plugins and call them with the signature ``checker(problem,
    warn=warn, headless=headless)``.

    .. note::
        The *warn* parameter is actually an integer. If it's nonzero,
        ``max(2, warn)`` is used to calculate the *stacklevel* passed to
        `~warnings.warn()`. Higher values push the reported offending
        location further up the stack trace.
    """
    unwrapped_env = getattr(env, "unwrapped", None)
    assert unwrapped_env is not None, f'missing property "unwrapped" on {type(env)}'
    assert isinstance(
        unwrapped_env, Problem
    ), f"{type(unwrapped_env)} must inherit from Problem"
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
    entry_points = importlib_metadata.entry_points().select(group="cernml.coi.checkers")
    # Run plug-in checkers.
    for entry_point in entry_points:
        LOG.debug("Loading checker plugin %s", entry_point.name)
        check_extra = entry_point.load()
        LOG.debug("Running checker plugin %s on %s", entry_point.name, env)
        check_extra(env, warn=warn, headless=headless)
