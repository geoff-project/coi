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

## Matplotlib Utilities

The following functions and types are only available if the
[Matplotlib](https://matplotlib.org/) is importable.

```eval_rst
.. autofunction:: cernml.coi.mpl_utils.iter_matplotlib_figures

.. autoclass:: cernml.coi.unstable.renderer.Renderer
    :members:
    :show-inheritance:

    .. warning::
        This class is considered *unstable* and may change arbitrarily between
        minor releases.

.. autoclass:: cernml.coi.unstable.renderer.SimpleRenderer
    :members:
    :show-inheritance:

    .. warning::
        This class is considered *unstable* and may change arbitrarily between
        minor releases.

.. autodecorator:: cernml.coi.unstable.renderer.render_generator

    .. warning::
        This decorator is considered *unstable* and may change arbitrarily
        between minor releases.
```

## Cancellation

```eval_rst
.. automodule:: cernml.coi.unstable.cancellation
    :members:
    :show-inheritance:

    .. warning::
        This module is considered *unstable* and may change arbitrarily
        between minor releases.
```

## PyJapc Utilities

The following functions and types are only available if
[PyJapc](https://gitlab.cern.ch/scripting-tools/pyjapc) is importable.

```eval_rst
.. autofunction:: cernml.coi.unstable.japc_utils.monitoring

    .. warning::
        This function is considered *unstable* and may change arbitrarily
        between minor releases.

.. autofunction:: cernml.coi.unstable.japc_utils.subscriptions

    .. warning::
        This function is considered *unstable* and may change arbitrarily
        between minor releases.

.. autofunction:: cernml.coi.unstable.japc_utils.subscribe_stream

    .. warning::
        This function is considered *unstable* and may change arbitrarily
        between minor releases.

.. autoclass:: cernml.coi.unstable.japc_utils.ParamStream
    :members:
    :inherited-members:

    .. warning::
        This class is considered *unstable* and may change arbitrarily between
        minor releases.

.. autoclass:: cernml.coi.unstable.japc_utils.ParamGroupStream
    :members:
    :inherited-members:

    .. warning::
        This class is considered *unstable* and may change arbitrarily between
        minor releases.

.. autoclass:: cernml.coi.unstable.japc_utils.Header
    :members:
    :undoc-members:
    :show-inheritance:

    .. warning::
        This class is considered *unstable* and may change arbitrarily between
        minor releases.

.. autoexception:: cernml.coi.unstable.japc_utils.StreamError

    .. warning::
        This exception is considered *unstable* and may change arbitrarily
        between minor releases.

.. autoexception:: cernml.coi.unstable.japc_utils.JavaException

    .. warning::
        This exception is considered *unstable* and may change arbitrarily
        between minor releases.
```
