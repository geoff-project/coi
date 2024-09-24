# SPDX-FileCopyrightText: 2020 - 2024 CERN
# SPDX-FileCopyrightText: 2023 - 2024 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

"""This is the API documentation for the Common Optimization Interfaces.

This documentation lists every function and every class, including every
method, that is stably supported by this project. It has been written in
such a way as to support both browsing and targeted lookups.
Nonetheless, new readers might feel more comfortable reading the
:doc:`/guide/index` first.

The documentation is sorted thematically. It begins by listing the
:doc:`classes`, which are what users are expected to interact with most
of the time. This includes `SingleOptimizable` and `gymnasium.Env`, the
base classes from which most user classes should derive. After that
comes :doc:`registration`, which is what users need to use both in order
to publish their optimization problems, and to instantiate them. The
next section covers :doc:`configurable`, a mechanism through which an
optimization problem may declare which parts of it can be configured via
a graphical application.

After these topics of general interest, the documentation covers more
specialized tools and conveniences provided by this package.
:doc:`cancellation` is a method through which optimization problems may
wait for incoming data in a way that can still be interrupted by the
user in a safe manner. :doc:`checkers` allow authors of optimization
problems to test their classes for compliance with certain restrictions
and assumptions that we place on the more general :doc:`Gymnasium API
<gym:README>`. After that, we list :doc:`sep_goal_env`, which contains
useful but less commonly used interfaces. The :doc:`intersections`
provide useful classes for when you want implement two interfaces at
once or want to assert that a class does so. Finally, for all users of
`static type checking`_, a large number of :doc:`typeguards` is provided
to narrow this package's interfaces as necessary.

.. _static type checking: https://mypy.readthedocs.io/en/stable/

The last two sections document implementation details of this package.
We don't expect the general user to read or even acknowledge them;
rather, they are provided for the curious and for contributors who want
to become more familiar with this package. The :doc:`protocols` document
the pure protocols upon which the :doc:`core classes <classes>` are
built. :doc:`machinery` describes in detail the internal classes that
make the package work the way it does.
"""

from . import cancellation
from ._classes import (
    Constraint,
    Env,
    FunctionOptimizable,
    HasNpRandom,
    ParamType,
    Problem,
    SingleOptimizable,
)
from ._custom_optimizer_provider import CustomOptimizerProvider
from ._custom_policy_provider import CustomPolicyProvider, Policy
from ._goalenv import (
    GoalEnv,
    GoalObs,
    GoalType,
)
from ._intersections import (
    OptEnv,
    OptGoalEnv,
    SeparableOptEnv,
    SeparableOptGoalEnv,
)
from ._machine import Machine
from ._sepenv import (
    ActType,
    InfoDict,
    ObsType,
    SeparableEnv,
    SeparableGoalEnv,
)
from ._typeguards import (
    AnyOptimizable,
    is_configurable,
    is_configurable_class,
    is_custom_optimizer_provider,
    is_custom_optimizer_provider_class,
    is_env,
    is_env_class,
    is_function_optimizable,
    is_function_optimizable_class,
    is_goal_env,
    is_goal_env_class,
    is_optimizable,
    is_optimizable_class,
    is_problem,
    is_problem_class,
    is_separable_env,
    is_separable_env_class,
    is_separable_goal_env,
    is_separable_goal_env_class,
    is_single_optimizable,
    is_single_optimizable_class,
)
from .checkers import check
from .configurable import (
    BadConfig,
    Config,
    Configurable,
    ConfigValues,
    DuplicateConfig,
)
from .registration import (
    make,
    make_vec,
    pprint_registry,
    register,
    register_envs,
    registry,
    spec,
)

__all__ = (
    "ActType",
    "AnyOptimizable",
    "BadConfig",
    "Config",
    "ConfigValues",
    "Configurable",
    "Constraint",
    "CustomOptimizerProvider",
    "CustomPolicyProvider",
    "DuplicateConfig",
    "Env",
    "FunctionOptimizable",
    "GoalEnv",
    "GoalObs",
    "GoalType",
    "HasNpRandom",
    "InfoDict",
    "Machine",
    "ObsType",
    "OptEnv",
    "OptGoalEnv",
    "Policy",
    "ParamType",
    "Problem",
    "SeparableEnv",
    "SeparableGoalEnv",
    "SeparableOptEnv",
    "SeparableOptGoalEnv",
    "SingleOptimizable",
    "cancellation",
    "check",
    "checkers",
    "configurable",
    "is_configurable",
    "is_configurable_class",
    "is_custom_optimizer_provider",
    "is_custom_optimizer_provider_class",
    "is_env",
    "is_env_class",
    "is_function_optimizable",
    "is_function_optimizable_class",
    "is_goal_env",
    "is_goal_env_class",
    "is_optimizable",
    "is_optimizable_class",
    "is_problem",
    "is_problem_class",
    "is_separable_env",
    "is_separable_env_class",
    "is_separable_goal_env",
    "is_separable_goal_env_class",
    "is_single_optimizable",
    "is_single_optimizable_class",
    "make",
    "make_vec",
    "pprint_registry",
    "protocols",
    "register",
    "register_envs",
    "registry",
    "spec",
)
