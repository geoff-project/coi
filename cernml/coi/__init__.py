#!/usr/bin/env python3
"""Common Optimization Interface that abstracts over optimizers and RL agents.

The most primitive interface provided by this package is the `Problem`, and it
isn't very interesting on its own. More important are two interfaces that
extend `Problem`:

- `Env`, as provided by the `gym` package;
- `SingleOptimizable`, provided by this package.

The former is implemented by classes that describe reinforcement learning (RL)
problems; the latter by classes that describe numerical-optimization problems.
A class may implement both, either explicitly or through the convenience class
`OptEnv`.

This package comes with its own registry, similar to that of
`gym.envs.registration`. This makes it possible to globally register both RL
and numerical-optimization problems in one common list. To make your problem
usable, don't forget to call `coi.register(name, entry_point=Class)` after your
class definition.

For reasons of portability, this API does not support the full range of
`gym.Env` classes, but rather puts several restrictions on them. This is
inspired by `stable_baselines3.common.env_checker.check_env`, but comes with
additional requirements:

1. The `observation_space`, `action_space` and `optimization_space` must all be
   `gym.spaces.Box`es. The only exception is if the environment is a
   `gym.GoalEnv`: in that case, `observation_space` must be `gym.spaces.Dict`
   (with exactly the three expected keys) and the `'observation'` sub-space
   must be a `Box`.

2. The `action_space` and the `optimization_space` must have the same shape;
   They must only differ in their bounds. The bounds of the action space must
   be symmetric around zero and normalized (equal to or less than one).

3. The supported render modes must at least be `'ansi'` and `'qtembed'`. The
   call `env.render('ansi')` must return a string that contains a string
   representation of the environment's current state. The mode `'qtembed` has
   yet to be specified, but it will allow visualizing the state embedded into a
   PyQt application.

4. The environment metadata must contain a key `cern.machine` with a value of
   type `Machine`. It tells users which CERN accelerator the environment
   belongs to.

5. The reward range must be defined and rewards must always lie within it.
   (Depending on feedback, this restriction may be lifted later.)

6. The objective range must be defined and the loss returned by
   `compute_single_objective()` must always lie within it. (Depending on
   feedback, this restriction may be lifted later.)

7. The environment must never diverge to NaN or infinity.
"""

from ._configurable import (
    BadConfig,
    Config,
    Configurable,
    DuplicateConfig,
)
from ._env_checker import check_env
from ._machine import Machine
from ._optenv import (
    Constraint,
    OptEnv,
    OptGoalEnv,
    SingleOptimizable,
)
from ._problem import Problem
from ._registration import (
    registry,
    register,
    make,
    spec,
)
from ._sepenv import (
    SeparableEnv,
    SeparableGoalEnv,
    SeparableOptEnv,
    SeparableOptGoalEnv,
)

__version__ = "0.3.1"
