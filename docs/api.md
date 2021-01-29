# API Reference

## Common Optimization Interfaces

```eval_rst
.. autoclass:: cernml.coi.Machine
    :members:
    :undoc-members:
    :show-inheritance:

.. autoclass:: cernml.coi.Problem
    :members:
    :show-inheritance:

.. autoclass:: cernml.coi.SingleOptimizable
    :members:
    :show-inheritance:

.. autoclass:: gym.Env
    :members:
    :show-inheritance:

.. autoclass:: gym.GoalEnv
    :members:
    :show-inheritance:
```

## Spaces

```eval_rst
.. autoclass:: gym.spaces.Space
    :members:
    :undoc-members:
    :show-inheritance:

.. autoclass:: gym.spaces.Box
    :members:
    :undoc-members:
    :show-inheritance:
```

## Configuration of Problems

```eval_rst
.. autoclass:: cernml.coi.Configurable
    :members:
    :show-inheritance:

.. autoclass:: cernml.coi.Config
    :members: add, validate, validate_all
    :show-inheritance:
```

## Problem Registry

```eval_rst
.. autofunction:: cernml.coi.register

.. autofunction:: cernml.coi.make

.. autofunction:: cernml.coi.spec

.. autodata:: cernml.coi.registry

.. autoclass:: gym.envs.registration.EnvRegistry
    :members:
    :show-inheritance:
```

## Separable Environments

```eval_rst
.. autoclass:: cernml.coi.SeparableEnv
    :members:
    :show-inheritance:

.. autoclass:: cernml.coi.SeparableGoalEnv
    :members:
    :show-inheritance:

.. autoclass:: cernml.coi.OptEnv
    :members:
    :show-inheritance:

.. autoclass:: cernml.coi.OptGoalEnv
    :members:
    :show-inheritance:

.. autoclass:: cernml.coi.SeparableOptEnv
    :members:
    :show-inheritance:

.. autoclass:: cernml.coi.SeparableOptGoalEnv
    :members:
    :show-inheritance:
```

## Problem checkers

```eval_rst
.. autofunction:: cernml.coi.check

.. autofunction:: cernml.coi.checkers.check_problem

.. autofunction:: cernml.coi.checkers.check_single_optimizable

.. autofunction:: cernml.coi.checkers.check_env
```

## Utilities

```eval_rst
.. autofunction:: cernml.coi.utils.iter_matplotlib_figures
```
