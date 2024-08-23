..
    SPDX-FileCopyrightText: 2020-2024 CERN
    SPDX-FileCopyrightText: 2023-2024 GSI Helmholtzzentrum für Schwerionenforschung
    SPDX-FileNotice: All rights not expressly granted are reserved.

    SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

More Optimization Interfaces
============================

.. currentmodule:: cernml.coi

This section introduces a few interfaces that are sometimes useful, but often
appear under somewhat niche circumstances.

Multi-Goal Environments
-----------------------

.. digraph:: inheritance_diagram
    :caption: Fig. 2: Inheritance diagram of multi-goal environments.

    rankdir = "BT";
    bgcolor = "#00000000";
    node [shape=plaintext, fontname="Open Sans", style=filled, fillcolor="white"];
    edge [style=dashed];

    node[color=gray, fontcolor=gray];

    problem[shape=rectangle, label=<cernml.coi.<b>Problem</b>>];
    sopt[shape=rectangle, label=<cernml.coi.<b>SingleOptimizable</b>>];
    env[shape=rectangle, label=<gymnasium.<b>Env</b>>];

    node[color=black, fontcolor=black];
    goalenv[label=<
        <table border="0" cellborder="1" cellspacing="0" cellpadding="4">
            <tr><td>gymnasium_robotics.<b>GoalEnv</b></td></tr>
            <tr>
                <td>compute_reward(<i>achieved</i>: Obs, <i>desired</i
                >: Obs, <i>info</i>: Dict) → float<br
                />compute_terminated(<i>achieved</i>: Obs, <i>desired</i
                >: Obs, <i>info</i>: Dict) → float<br
                />compute_truncated(<i>achieved</i>: Obs, <i>desired</i
                >: Obs, <i>info</i>: Dict) → float</td>
            </tr>
        </table>
    >];

    {sopt env} -> problem;
    goalenv -> env;

In older versions of :doc:`Gymnasium <gym:README>`, the ``GoalEnv`` interface
was provided as an API for multi-goal RL. This class has since moved to the
:doc:`gymnasium-robotics <gymrob:README>` package. For backwards compatibility,
the class is still provided by this package under the name
`cernml.coi.GoalEnv`. If the gymnasium-robotics package is installed, its
implementation is re-exported directly. If not, an implementation is provided
by this package itself.

`GoalEnv` is a subclass of `Env` that extends the interface as follows:

- The *observation space* is required to always be a `~gymnasium.spaces.Dict`
  space with at least the keys ``"observation"``, ``"achieved_goal"`` and
  ``"desired_goal"``.

- the :func:`gymnasium.Env.step()` method is expected to calculate the return
  values *reward*, *terminated* and *truncated* through helper functions
  :func:`~gymnasium_robotics.core.GoalEnv.compute_reward()`,
  :func:`~gymnasium_robotics.core.GoalEnv.compute_terminated()` and
  :func:`~gymnasium_robotics.core.GoalEnv.compute_truncated()`. Suitable RL
  algorithms may use these functions to recalculate these values with different
  goal arguments.

Fully Separable Environments
----------------------------

.. digraph:: inheritance_diagram
    :caption: Fig. 3: Inheritance diagram of the separable-environment
        interfaces.

    rankdir = "BT";
    bgcolor = "#00000000";
    node [shape=plaintext, fontname="Open Sans", style=filled, fillcolor="white"];
    edge [style=dashed];

    node[color=gray, fontcolor=gray];
    problem[shape=rectangle, label=<cernml.coi.<b>Problem</b>>];
    sopt[shape=rectangle, label=<cernml.coi.<b>SingleOptimizable</b>>];
    env[shape=rectangle, label=<gymnasium.<b>Env</b>>];
    goalenv[label=<
        <table border="0" cellborder="1" cellspacing="0" cellpadding="4">
            <tr><td>gymnasium_robotics.<b>GoalEnv</b></td></tr>
            <tr>
                <td>compute_reward(<i>achieved</i>: Obs, <i>desired</i
                >: Obs, <i>info</i>: Dict) → float<br
                />compute_terminated(<i>achieved</i>: Obs, <i>desired</i
                >: Obs, <i>info</i>: Dict) → float<br
                />compute_truncated(<i>achieved</i>: Obs, <i>desired</i
                >: Obs, <i>info</i>: Dict) → float</td>
            </tr>
        </table>
    >];

    node[color=black, fontcolor=black];
    sepenv[label=<
        <table border="0" cellborder="1" cellspacing="0" cellpadding="4">
            <tr><td>cernml.coi.<b>SeparableEnv</b></td></tr>
            <tr>
                <td>compute_observation(<i>action</i>: Action, <i>info</i
                >: Dict) → float<br
                />compute_reward(<i>achieved</i>: Obs, <i>desired</i
                >: None, <i>info</i>: Dict) → float<br
                />compute_terminated(<i>achieved</i>: Obs, <i>reward</i
                >: float, <i>info</i>: Dict) → float<br
                />compute_truncated(<i>achieved</i>: Obs, <i>reward</i
                >: float, <i>info</i>: Dict) → float</td>
            </tr>
        </table>
    >];
    sepgoalenv[label=<
        <table border="0" cellborder="1" cellspacing="0" cellpadding="4">
            <tr><td>cernml.coi.<b>SeparableGoalEnv</b></td></tr>
            <tr>
                <td>compute_observation(<i>action</i>: Action, <i>info</i
                >: Dict) → float</td>
            </tr>
        </table>
    >];

    {sopt env} -> problem;
    sepenv -> env;
    sepgoalenv -> goalenv -> env;

Many environments in a particle accelerator context are very simple: their
rewards do not depend explictly on time and the end of the episode can be
determined in a side-effect-free manner.

Such environments may expose this fact through the `SeparableEnv` interface.
This is useful to e.g. calculate the reward that would correspond to the
initial observation. (if there *were* a reward to associate with it.)

The `SeparableEnv` interface implements `~SeparableEnv.step()` for you by means
of four new abstract methods: `~SeparableEnv.compute_observation()`,
`~SeparableEnv.compute_reward()`, `~SeparableEnv.compute_terminated()` and
`~SeparableEnv.compute_truncated()`.

Similarly, `SeparableGoalEnv` adds `~SeparableGoalEnv.compute_observation()` to
the methods already defined by `GoalEnv`. It also provides a default
implementation of `~SeparableGoalEnv.step()`.

The main distinguishing property between the two interfaces is that
`SeparableGoalEnv` still requires the observation space to adhere to the
`GoalEnv` requirements; `SeparableEnv` has no such restrictions.

One quirk of the `SeparableEnv` interface is that
`~SeparableEnv.compute_reward()` takes a dummy parameter *desired* that must
always be None. This is for compatibility with `GoalEnv`, ensuring that both
methods have the same signature. This makes it easier to write generic code
that can handle both interfaces equally well.

Intersection Interfaces
-----------------------

.. seealso::

    :doc:`/api/typeguards`
        API reference for functions that let you test whether a given object
        implements an interface or not.

.. digraph:: inheritance_diagram
    :caption: Fig. 4: Inheritance diagram of intersection interfaces.

    rankdir = "BT";
    bgcolor = "#00000000";
    node [shape=plaintext, fontname="Open Sans", style=filled, fillcolor="white"];
    edge [style=dashed];

    node[color=gray, fontcolor=gray, shape=rectangle];
    problem[label=<cernml.coi.<b>Problem</b>>];

    subgraph cluster_base {
        style=invis;
        sopt[label=<cernml.coi.<b>SingleOptimizable</b>>];
        env[label=<gymnasium.<b>Env</b>>];
    }

    goalenv[label=<gynasium_robotics.<b>GoalEnv</b>>];
    sepenv[label=<cernml.coi.<b>SeparableEnv</b>>];
    sepgoalenv[label=<cernml.coi.<b>SeparableGoalEnv</b>>];

    node[color=black, fontcolor=black];
    optenv[label=<cernml.coi.<b>OptEnv</b>>];
    optgoalenv[label=<cernml.coi.<b>OptGoalEnv</b>>];
    sepoptenv[label=<cernml.coi.<b>SeparableOptEnv</b>>];
    sepoptgoalenv[label=<cernml.coi.<b>SeparableOptGoalEnv</b>>];

    optenv -> {sopt env} -> problem;
    {goalenv sepenv} -> env;
    optgoalenv -> {optenv goalenv};
    sepgoalenv -> goalenv;
    sepoptenv -> {optenv sepenv};
    sepoptgoalenv -> {sepgoalenv optgoalenv};

If you want to either implement multiple of :doc:`the core classes of this
package <core>`, or you want to require that a problem implement multiple of
them, this package provides a number of interfaces that represent
*intersections* of them:

- `OptEnv` is an intersection of `SingleOptimizable` and `Env`;
- `OptGoalEnv` is an intersection of `SingleOptimizable` and `GoalEnv`;
- `SeparableOptEnv` is an intersection of `SingleOptimizable` and
  `SeparableEnv`;
- `SeparableOptGoalEnv` is an intersection of `SingleOptimizable` and
  `SeparableGoalEnv`.

Taking for example `OptEnv`, you can shorten your line of base classes:

.. code-block:: python

    >>> from gymnasium.spaces import Box
    >>> from gymnasium import Env
    >>> from cernml import coi
    ...
    >>> class Both(coi.OptEnv):
    ...     def __init__(self, render_mode=None):
    ...         super().__init__(render_mode)
    ...         self.optimization_space = Box(-1, 1)
    ...         self.observation_space = Box(-1, 1)
    ...         self.action_space = Box(-1, 1)
    ...
    ...     def get_initial_params(self): ...
    ...     def compute_single_objective(self, params): ...
    ...     def reset(self, *, seed=None, options=None): ...
    ...     def step(self, action): ...
    ...
    >>> env = Both()
    >>> isinstance(env, coi.SingleOptimizable)
    True
    >>> isinstance(env, Env)
    True
    >>> isinstance(env, coi.OptEnv)
    True

Vice versa, you can use it to test if a class implements both
`SingleOptimizable` and `Env`, *even if* it doesn't subclass `OptEnv` itself:

.. code-block:: python

    >>> class Indirect(Env, coi.SingleOptimizable):
    ...     def __init__(self, render_mode=None):
    ...         super().__init__(render_mode)
    ...         self.optimization_space = Box(-1, 1)
    ...         self.observation_space = Box(-1, 1)
    ...         self.action_space = Box(-1, 1)
    ...
    ...     def get_initial_params(self): ...
    ...
    ...     def compute_single_objective(self, params): ...
    ...
    >>> env = Indirect()
    >>> isinstance(env, coi.SingleOptimizable)
    True
    >>> isinstance(env, Env)
    True
    >>> isinstance(env, coi.OptEnv)
    True

The intersection classes come with a few limitations that can't be avoided:

- In order to be recognized, a class *must* inherit from `Env` or one its
  subclasses introduced in this section. Just defining the same set of methods
  is not enough.

- Static type checkers like MyPy_ generally don't recognize the
  intersections as `protocols <Protocol>`.

- Checks via :func:`issubclass()` only work if you either:

  1. inherit from one of the intersections,
  2. define all three spaces (`~SingleOptimizable.optimization_space`,
     `~gymnasium.Env.observation_space`, `~gymnasium.Env.action_space`) at
     class scope (even if those definitions are just dummies),
  3. define all three spaces via `property`.

  By contrast, :func:`isinstance()` always works, even if the spaces are only
  defined in :meth:`~object.__init__()`.

.. _MyPy: https://mypy.readthedocs.io/
