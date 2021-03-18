"""Common Optimization Interfaces for optimizers and RL agents.

The most primitive interface provided by this package is the
:py:class:`Problem`, and it isn't very interesting on its own. More
important are two interfaces that extend :py:class:`Problem`:

- :py:class:`gym.Env`, as provided by `OpenAI Gym`_;
- :py:class:`SingleOptimizable`, provided by this package.

.. _OpenAI Gym: https://github.com/openai/gym/

The former is implemented by classes that describe reinforcement
learning (RL) problems; the latter by classes that describe
numerical-optimization problems. A class may implement both, either
explicitly or through the convenience class :py:class:`OptEnv`.

This package comes with its own registry, similar to that of
:py:mod:`gym.envs.registration`. This makes it possible to globally
register both RL and numerical-optimization problems in one common list.
To make your problem findable by other applications, don't forget to
call ``coi.register(name, entry_point=Class)`` after your class
definition.

For reasons of portability, this API does not support the full range of
:py:class:`gym.Env` classes, but rather puts several restrictions on
them. This is inspired by `Stable Baselines' Env Checker`_, but comes
with additional requirements. For more information, please refer to `our
package docs`_.

.. _Stable Baselines' Env Checker: https://stable-baselines3.readthedocs.io/en/master/common/env_checker.html
.. _our package docs: https://acc-py.web.cern.ch/gitlab/be-op-ml-optimization/cernml-coi
"""

from ._cancellation import CancellationToken, CancellationTokenSource, CancelledError
from ._configurable import BadConfig, Config, Configurable, DuplicateConfig
from ._machine import Machine
from ._optenv import Constraint, OptEnv, OptGoalEnv, SingleOptimizable
from ._problem import Problem
from ._registration import make, register, registry, spec
from ._sepenv import (
    SeparableEnv,
    SeparableGoalEnv,
    SeparableOptEnv,
    SeparableOptGoalEnv,
)
from .checkers import check

__version__: str
try:
    from ._version import VERSION as __version__  # type: ignore
except ImportError:
    from setuptools_scm import get_version

    try:
        __version__ = get_version()
    finally:
        del get_version
