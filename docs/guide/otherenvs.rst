..
    SPDX-FileCopyrightText: 2020-2024 CERN
    SPDX-FileCopyrightText: 2023-2024 GSI Helmholtzzentrum für Schwerionenforschung
    SPDX-FileNotice: All rights not expressly granted are reserved.

    SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

More Optimization Interfaces
============================

.. currentmodule:: cernml.coi

This section introduces a few useful, but less common interfaces defined by Gym
and the COI.

Configurable
------------

.. digraph:: control_flow
    :caption: Fig. 1: Sequence diagram of the Configurable API

    newrank = true;
    node[shape=box, style=rounded];

    subgraph cluster_user {
        label = "User";
        configure[label="Configure problem"];
        modify[label="Modify values"];
        submit[label="Submit new values"];
        end[label="Present success/failure"];
    }

    subgraph cluster_host {
        label = "Host";
        get_config[label="problem.get_config()"];
        get_field_values[label="config.get_field_values()"];
        validate[label="config.validate_all(values)"];
        apply_config[label="problem.apply_config(validated)"];
        return_host[label="return", shape=plaintext];
    }

    subgraph cluster_plugin {
        label = "Plugin";
        make_config[label="Config().add(…).add(…)"];
        return_config[label="return config", shape=plaintext];
        use_config[label="self.field = validated.field"];
        return_none[label="return", shape=plaintext];
    }

    { rank=same; configure; get_config; make_config; }
    { rank=same; modify; get_field_values; return_config; }
    { rank=same; submit; validate; }
    { rank=same; apply_config; use_config; }
    { rank=same; end; return_host; return_none; }

    configure -> get_config -> make_config;
    make_config -> return_config;
    return_config -> get_field_values -> modify [style=dashed];
    modify -> submit;
    submit -> validate;
    validate -> apply_config;
    apply_config -> use_config;
    use_config -> return_none;
    return_none -> return_host -> end [style=dashed];

The *Configurable* API provides a uniform way for problem authors to declare
parameters of their class that can be modified before (but not during) an
optimization run. It also allows specifying certain variants for each
parameter. Host applications can use this interface to present a configuration
dialog to the user.

Usage examples are shown in the API reference for `Configurable`.

CustomOptimizerProvider
-----------------------

There are situations when it is desirable to use an optimization algorithm that
is custom-tailored towards a specific optimization problem. It doesn't make
sense to offer this algorithm for all problems, e.g. because its defaults are
specially adjusted for only that problem.

For this purpose, you can declare a *custom optimizer provider*. This provider
is queried by host applications when putting together the list of available
optimization algorithms. The optimizers that it returns are added to the list
if the provider is appropriate for the selected optimization problem.

There are two ways to declare a custom optimizer provider:

1. Your optimization problem defines the
   `~CustomOptimizerProvider.get_optimizers()` method of the
   `CustomOptimizerProvider` abstract base class.

2. You define an an :doc:`entry point <pkg:specifications/entry-points>` in the
   group ``cernml.custom_optimizers`` that has the same `registry` name as the
   optimization problem that it is appropriate for. This entry point should
   either point at a subclass of `CustomOptimizerProvider` or at a bare
   function that acts like `~CustomOptimizerProvider.get_optimizers()`.

Examples for both approaches are shown below.

.. tab:: Entry points (pyproject.toml)

   .. code-block:: toml

        # pyproject.toml

        [project.entry-points.'cernml.envs']
        MyOptimizationProblem-v1 = 'mypackage:MyEnv1'
        MyOptimizationProblem-v2 = 'mypackage:MyEnv2'

        [project.entry-points.'cernml.custom_optimizers']
        MyOptimizationProblem-v1 = 'mypackage:ProviderClass'
        MyOptimizationProblem-v2 = 'mypackage:provider_func'

   .. code-block:: py

        # mypackage/__init__.py

        from cernml import coi

        class MyEnv1(coi.SingleOptimizable): ...

        class MyEnv2(coi.OptEnv): ...

        class ProviderClass(coi.CustomOptimizerProvider):
            @classmethod
            def get_optimizers(cls):
                return {"MyCustomOptimizer-v1": ...}

        def provider_func():
                return {"MyCustomOptimizer-v2": ...}

.. tab:: Entry points (setup.cfg)

   .. code-block:: cfg

        # setup.cfg

        [options.entry_points]
        cernml.envs =
            MyOptimizationProblem-v1 = mypackage:MyEnv1
            MyOptimizationProblem-v2 = mypackage:MyEnv2
        cernml.custom_optimizers =
            MyOptimizationProblem-v1 = mypackage:ProviderClass
            MyOptimizationProblem-v2 = mypackage:provider_func

   .. code-block:: py

        # mypackage/__init__.py

        from cernml import coi

        class MyEnv1(coi.SingleOptimizable): ...

        class MyEnv2(coi.OptEnv): ...

        class ProviderClass(coi.CustomOptimizerProvider):
            @classmethod
            def get_optimizers(cls):
                return {"MyCustomOptimizer-v1": ...}

        def provider_func():
                return {"MyCustomOptimizer-v2": ...}

.. tab:: Entry points (setup.py)

   .. code-block:: py

        # setup.py

        from setuptools import setup

        # ...

        setup(
            # ...,
            entry_points={
                "cernml.envs": [
                    "MyOptimizationProblem-v1 = mypackage:MyEnv1",
                    "MyOptimizationProblem-v2 = mypackage:MyEnv2",
                ],
                "cernml.custom_optimizers": [
                    "MyOptimizationProblem-v1 = mypackage:ProviderClass",
                    "MyOptimizationProblem-v2 = mypackage:provider_func",
                ],
            },
        )

   .. code-block:: py

        # mypackage/__init__.py

        from cernml import coi

        class MyEnv1(coi.SingleOptimizable): ...

        class MyEnv2(coi.OptEnv): ...

        class ProviderClass(coi.CustomOptimizerProvider):
            @classmethod
            def get_optimizers(cls):
                return {"MyCustomOptimizer-v1": ...}

        def provider_func():
                return {"MyCustomOptimizer-v2": ...}

.. tab:: Inheritance

   .. code-block:: py

        # mypackage/__init__.py

        from cernml import coi

        class MyEnv1(coi.SingleOptimizable, coi.CustomOptimizerProvider):

            # ...

            @classmethod
            def get_optimizers(cls):
                return {"MyCustomOptimizer-v1": ...}

        coi.register("MyOptimizationProblem-v1", entry_point=MyEnv1)

        class MyEnv2(coi.OptEnv, coi.CustomOptimizerProvider):

            # ...

            @classmethod
            def get_optimizers(cls):
                return {"MyCustomOptimizer-v2": ...}

        coi.register("MyOptimizationProblem-v2", entry_point=MyEnv2)

GoalEnv
-------

.. digraph:: inheritance_diagram
    :caption: Fig. 2: Inheritance diagram of multi-goal environments

    rankdir = "BT";
    bgcolor = "#00000000";
    node [shape=record, fontname="Latin Modern Sans", style=filled, fillcolor="white"];
    edge [style=dashed];

    node[color=gray, fontcolor=gray];

    problem[shape=rectangle, label=<cernml.coi.<b>Problem</b>>];
    sopt[shape=rectangle, label=<cernml.coi.<b>SingleOptimizable</b>>];
    env[shape=rectangle, label=<gym.<b>Env</b>>];
    optenv[label=<cernml.coi.<b>OptEnv</b>>];

    node[color=black, fontcolor=black];
    goalenv[label=<{
        gym.<b>GoalEnv</b>|
        compute_reward(<i>achieved</i>: Obs, <i>desired</i>: Obs, <i>info</i>: Dict) → float}>,
    ];

    optgoalenv[label=<cernml.coi.<b>OptGoalEnv</b>>];

    optenv -> sopt -> problem;
    optenv -> env -> problem;
    optgoalenv -> goalenv -> env;
    optgoalenv -> sopt;

Gym provides `~gym.GoalEnv` as a specialization of `~gym.Env`. To accommodate
it, this package also provides `OptGoalEnv` as a similar abstract base class
for everything that inherits both from `SingleOptimizable` and from
`~gym.GoalEnv`.

SeparableEnv
------------

.. digraph:: inheritance_diagram
    :caption: Fig. 3: Inheritance diagram of the separable-environment interfaces

    rankdir = "BT";
    bgcolor = "#00000000";
    node [shape=record, fontname="Latin Modern Sans", style=filled, fillcolor="white"];
    edge [style=dashed];

    node[color=gray, fontcolor=gray];
    env[shape=rectangle, label=<gym.<b>Env</b>>];
    goalenv[label=<{
        gym.<b>GoalEnv</b>|
        compute_reward(<i>achieved</i>: Obs, <i>desired</i>: Obs, <i>info</i>: Dict) → float}>,
    ];

    node[color=black, fontcolor=black];
    sepenv[label=<{
        gym.<b>SeparableEnv</b>|
        compute_observation(<i>action</i>: Action, <i>info</i>: Dict) →
        float<br/>compute_reward(<i>achieved</i>: Obs, <i>desired</i>: None, <i>info</i>: Dict) → float<br/>compute_done(<i>achieved</i>: Obs, <i>reward</i>: float, <i>info</i>: Dict) → float}>,
    ];
    sepgoalenv[label=<{
        gym.<b>SeparableGoalEnv</b>|
        compute_observation(<i>action</i>: Action, <i>info</i>: Dict) →
        float<br/>compute_done(<i>achieved</i>: Obs, <i>reward</i>: float, <i>info</i>: Dict) → float}>,
    ];

    sepenv -> env;
    sepgoalenv -> goalenv -> env;

Many environments in a particle accelerator context are very simple: their
rewards do not depend explictly on time and the end of the episode can be
determined in a side-effect-free manner.

Such environments may expose this fact through the `SeparableEnv` interface.
This is useful to e.g. calculate the reward that would correspond to the
initial observation. (if there *were* a reward to associate with it.)

The `SeparableEnv` interface implements `Env.step() <SeparableEnv.step()>` for
you by means of three new abstract methods:
`~SeparableEnv.compute_observation()`, `~SeparableEnv.compute_reward()` and
`~SeparableEnv.compute_done()`.

Similarly, `SeparableGoalEnv` adds `~SeparableGoalEnv.compute_observation()`
and `~SeparableGoalEnv.compute_done()` in addition to the already existing
`~gym.GoalEnv.compute_reward()`.

One quirk of this interface is that `~SeparableEnv.compute_reward()` takes
a dummy parameter *desired* that must always be None. This is for compatibility
with `~gym.GoalEnv`, ensuring that both methods have the same signature. This
makes it easier to write generic code that can handle both interfaces equally
well.

In an analogous manner to `OptEnv`, convenience base classes exist that combine
each of the separable interfaces with `SingleOptimizable`. They are
`SeparableOptEnv`, and `SeparableOptGoalEnv`.
