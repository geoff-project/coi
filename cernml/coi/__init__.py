#!/usr/bin/env python3
"""Common Optimization Interface that abstracts over optimizers and RL agents.

# Motivation

Several problems in accelerator control can be solved both using reinforcement
learning (RL) and numerical optimization. However, both approaches usually
slightly differ in their expected input and output:

- Num. optimizers pick certain _points_ in the phase space of modifiable
  parameters and evaluate the loss of these parameters. They minimize this loss
  through multiple evaluations and ultimately yield the optimal parameters.
- RL agents assume that the problem has a certain state, which usually contains
  the values of all modifiable parameters. They receive an observation (which
  is usually higher-dimensional than the loss) and calculate a _correction_ of
  the parameters. This correction yields a certain reward to them. Their goal
  is to optimize the parameters incrementally by optimzing their corrections
  for maximal reward.

More informally, num. optimizers start from scratch each time they are applied
and they yield a point in phase space. RL agents learn once, can be applied
many times, and they yield a sequence of deltas in the phase space.

Even more informally, on a given machine, a num. optimizer performs the
state transition `machine.parameters = new_parameters`, whereas an RL agent
performs the state transition `machine.parameters += corrections` iteratively.

This package provides interfaces to implement for problems that should be
compatible both with num. optimizers and RL agents. It is based on the [Gym][]
environment API and enhances it with the `Optimizable` interface. In addition,
the output and metadata of the environments is _restricted_ to make the
behavior of environments more uniform and compatible to make them more easily
visualizable and integrable into a generic machine-optimization application.

[Gym]: https://github.com/openai/gym/

# The API

The core interface is `Optimizable`, which can be implemented by any class that
can be used with num. optimizers. Each class that describes a compatible
problem should inherit both from `Optimizable` and from `gym.Env`. For
convenience, the helper classes `OptEnv` and `OptGoalEnv` are provided, which
already inherit from the two. Compatible classes then must implement these
interfaces according to their specifications. This API makes the following
additional restrictions:

- The `observation_space`, `action_space` and `optimization_space` must all be
  `gym.spaces.Box`es. The only exception is if the environment is a
  `gym.GoalEnv`: in that case, `observation_space` must be `gym.spaces.Dict`
  (with exactly the three expected keys) and the `'observation'` sub-space must
  be a `Box`.
- The `action_space` and the `optimization_space` must have the same shape;
  They must only differ in their bounds. The bounds of the action space must be
  symmetric around zero and normalized (equal to or less than one).
- The supported render modes must at least be `'ansi'` and `'qtembed'`. The
  call `env.render('ansi')` must return a string that contains a string
  represnetation of the environment's current state. The mode `'qtembed` has
  yet to be specified, but it will allow visualizing the state embedded into a
  PyQt application.
- The environment metadata must contain a key `cern.machine` with a value of
  type `Machine`. It tells users which CERN accelerator the environment belongs
  to.
- The reward range must be defined and rewards must always lie within it.
  (Depending on feedback, this restriction may be lifted later.)
- The environment must never diverge to NaN or infinity.
"""

from .env_checker import check_env
from .machine import Machine
from .optenv import Constraint, OptEnv, OptGoalEnv, SingleOptimizable
from .problem import Problem
from .registration import registry, register, make, spec
from .sepenv import (
    SeparableEnv,
    SeparableGoalEnv,
    SeparableOptEnv,
    SeparableOptGoalEnv,
)

__version__ = "0.2.1"
