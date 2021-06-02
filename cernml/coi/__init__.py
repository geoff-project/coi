"""Common Optimization Interfaces for optimizers and RL agents.

The most primitive interface provided by this package is the
:class:`Problem`, and it isn't very interesting on its own. More
important are three interfaces that extend :class:`Problem`:

- :class:`gym.Env`, as provided by `OpenAI Gym
  <https://github.com/openai/gym/>`_;
- :class:`SingleOptimizable` and :class:`FunctionOptimizable`, provided
  by this package.

The former is implemented by classes that describe reinforcement
learning (RL) problems; the latter by classes that describe
numerical-optimization problems. A class may implement both, either
explicitly or through the convenience class :class:`OptEnv`.

This package comes with its own registry, similar to that of
:mod:`gym.envs.registration`. This makes it possible to globally
register both RL and numerical-optimization problems in one common list.
To make your problem findable by other applications, don't forget to
call ``coi.register(name, entry_point=Class)`` after your class
definition.

For reasons of portability, this API does not support the full range of
:class:`~gym.Env` classes, but rather puts several restrictions on them.
This is inspired by `Stable Baselines' Env Checker
<https://stable-baselines3.readthedocs.io/en/master/common/env_checker.html>`_,
but comes with additional requirements. For more information, please
refer to `our package docs
<https://acc-py.web.cern.ch/gitlab/be-op-ml-optimization/cernml-coi>`_.
"""

from ._configurable import BadConfig, Config, Configurable, DuplicateConfig
from ._func_opt import FunctionOptimizable
from ._machine import Machine
from ._problem import Problem
from ._registration import make, register, registry, spec
from ._sepenv import SeparableEnv, SeparableGoalEnv
from ._single_opt import Constraint, SingleOptimizable
from ._union_interfaces import OptEnv, OptGoalEnv, SeparableOptEnv, SeparableOptGoalEnv
from .checkers import check

__all__ = [
    "BadConfig",
    "Config",
    "Configurable",
    "Constraint",
    "DuplicateConfig",
    "FunctionOptimizable",
    "Machine",
    "OptEnv",
    "OptGoalEnv",
    "Problem",
    "SeparableEnv",
    "SeparableGoalEnv",
    "SeparableOptEnv",
    "SeparableOptGoalEnv",
    "SingleOptimizable",
    "check",
    "checkers",
    "make",
    "register",
    "registry",
    "spec",
]
