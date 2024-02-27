# SPDX-FileCopyrightText: 2020-2024 CERN
# SPDX-FileCopyrightText: 2023-2024 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

"""Common Optimization Interfaces for optimizers and RL agents.

The most primitive interface provided by this package is the `Problem`,
and it isn't very interesting on its own. More important are three
interfaces that extend `Problem`:

- `gym.Env`, as provided by `OpenAI Gym
  <https://github.com/openai/gym/>`_;
- `SingleOptimizable` and `FunctionOptimizable`, provided by this
  package.

The former is implemented by classes that describe reinforcement
learning (RL) problems; the latter by classes that describe
numerical-optimization problems. A class may implement both, either
explicitly or through the convenience class `OptEnv`.

This package comes with its own :doc:`registry <registry>`; it is
similar to Gym's :class:`~gym.envs.registration.EnvRegistry`, but makes
it possible to register both RL and numerical-optimization problems in
one common list. To make your problem findable by other applications,
never forget the following line:

.. code-block:: python

    coi.register("name", entry_point=Class)

For reasons of portability, this API does not support the full range of
`~gym.Env` classes, but rather puts several restrictions on them. This
is inspired by the :doc:`sb3:common/env_checker` designed by
:doc:`Stable Baselines <sb3:index>`, but comes with additional
requirements. For more information, please refer to our
:doc:`/guide/index`.

Finally, for the purpose of embedding optimization problems as *plugins*
into a *host application*, this package also provides an interface for
pre-run :doc:`configuration <config>` of optimization problems and for
the :doc:`cancellation <cancellation>` of running algorithms.
"""

from ._configurable import (
    BadConfig,
    Config,
    Configurable,
    ConfigValues,
    DuplicateConfig,
)
from ._custom_optimizer_provider import CustomOptimizerProvider
from ._custom_policy_provider import CustomPolicyProvider, Policy
from ._extra_envs import OptEnv, SeparableEnv, SeparableOptEnv
from ._extra_goal_envs import OptGoalEnv, SeparableGoalEnv, SeparableOptGoalEnv
from ._func_opt import BaseFunctionOptimizable, FunctionOptimizable
from ._goalenv import GoalEnv
from ._machine import Machine
from ._problem import BaseProblem, HasNpRandom, Problem
from ._registration import make, register, registry, spec
from ._single_opt import BaseSingleOptimizable, Constraint, SingleOptimizable
from ._typeguards import (
    AnyOptimizable,
    is_function_optimizable,
    is_function_optimizable_class,
    is_optimizable,
    is_optimizable_class,
    is_problem,
    is_problem_class,
    is_single_optimizable,
    is_single_optimizable_class,
)
from .checkers import check

__all__ = [
    "AnyOptimizable",
    "BadConfig",
    "BaseFunctionOptimizable",
    "BaseProblem",
    "BaseSingleOptimizable",
    "Config",
    "ConfigValues",
    "Configurable",
    "Constraint",
    "CustomOptimizerProvider",
    "CustomPolicyProvider",
    "DuplicateConfig",
    "FunctionOptimizable",
    "GoalEnv",
    "HasNpRandom",
    "Machine",
    "OptEnv",
    "OptGoalEnv",
    "Policy",
    "Problem",
    "SeparableEnv",
    "SeparableGoalEnv",
    "SeparableOptEnv",
    "SeparableOptGoalEnv",
    "SingleOptimizable",
    "check",
    "checkers",
    "is_function_optimizable",
    "is_function_optimizable_class",
    "is_optimizable",
    "is_optimizable_class",
    "is_problem",
    "is_problem_class",
    "is_single_optimizable",
    "is_single_optimizable_class",
    "make",
    "register",
    "registry",
    "spec",
]
