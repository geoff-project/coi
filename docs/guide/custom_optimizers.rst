..
    SPDX-FileCopyrightText: 2020-2024 CERN
    SPDX-FileCopyrightText: 2023-2024 GSI Helmholtzzentrum für Schwerionenforschung
    SPDX-FileNotice: All rights not expressly granted are reserved.

    SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

Custom Per-Problem Optimizers
=============================

.. currentmodule:: cernml.coi

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
   `CustomOptimizerProvider` protocol.

2. You define an an entry point in the group :ep:`cernml.custom_optimizers`
   whose name is the :ref:`registry ID <guide/registration:Registry IDs>` of
   the matching optimization problem. This entry point should either point at
   a subclass of `CustomOptimizerProvider` or at a bare function that acts like
   `~CustomOptimizerProvider.get_optimizers()`.

Examples for both approaches are shown below.

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

.. tab:: Entry points (pyproject.toml)

   .. code-block:: toml

        # pyproject.toml

        [project.entry-points.'cernml.envs']
        MyNamespace = 'mypackage'

        [project.entry-points.'cernml.custom_optimizers']
        'MyNamespace/MyOptimizationProblem-v1' = 'mypackage:ProviderClass'
        'MyNamespace/MyOptimizationProblem-v2' = 'mypackage:provider_func'

   .. code-block:: py

        # mypackage/__init__.py

        from cernml import coi

        class MyEnv1(coi.SingleOptimizable): ...

        coi.register("MyNamespace/MyEnv1", MyEnv1)

        class MyEnv2(coi.OptEnv): ...

        coi.register("MyNamespace/MyEnv2", MyEnv2)

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
            MyNamespace = mypackage
        cernml.custom_optimizers =
            MyNamespace/MyOptimizationProblem-v1 = mypackage:ProviderClass
            MyNamespace/MyOptimizationProblem-v2 = mypackage:provider_func

   .. code-block:: py

        # mypackage/__init__.py

        from cernml import coi

        class MyEnv1(coi.SingleOptimizable): ...

        coi.register("MyNamespace/MyEnv1", MyEnv1)

        class MyEnv2(coi.OptEnv): ...

        coi.register("MyNamespace/MyEnv2", MyEnv2)

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
                    "MyNamespace = mypackage",
                ],
                "cernml.custom_optimizers": [
                    "MyNamespace/MyOptimizationProblem-v1 = mypackage:ProviderClass",
                    "MyNamespace/MyOptimizationProblem-v2 = mypackage:provider_func",
                ],
            },
        )

   .. code-block:: py

        # mypackage/__init__.py

        from cernml import coi

        class MyEnv1(coi.SingleOptimizable): ...

        coi.register("MyNamespace/MyEnv1", MyEnv1)

        class MyEnv2(coi.OptEnv): ...

        coi.register("MyNamespace/MyEnv2", MyEnv2)

        class ProviderClass(coi.CustomOptimizerProvider):
            @classmethod
            def get_optimizers(cls):
                return {"MyCustomOptimizer-v1": ...}

        def provider_func():
                return {"MyCustomOptimizer-v2": ...}

Custom Per-Environment Policies
-------------------------------

Similar to the custom optimizer providers, there are many cases in RL where an
algorithm is only really applicable to a single environment. For this purpose,
you can declare a *custom policy provider*. It works very similar to optimizer
providers, but differs in some aspects of its API.

There are two ways to declare a custom policy provider:

1. Your environment problem defines the
   `~CustomPolicyProvider.get_policy_names()` and
   `~CustomPolicyProvider.load_policy()` methods of the `CustomPolicyProvider`
   abstract base class.

2. You define an an entry point in the group :ep:`cernml.custom_policies` that
   has the same `registry` name as the environment that it is appropriate for.
   This entry point should point at a subclass of `CustomPolicyProvider` and
   that class should be instantiable by calling it with no arguments.

Examples for both approaches are shown below.

.. tab:: Entry points (pyproject.toml)

   .. code-block:: toml

        # pyproject.toml

        [project.entry-points.'cernml.envs']
        MyEnv-v1 = 'mypackage:MyEnv1'

        [project.entry-points.'cernml.custom_policies']
        MyEnv-v1 = 'mypackage:ProviderClass'

   .. code-block:: py

        # mypackage/__init__.py

        import gym
        from stable_baselines3 import TD3
        from cernml import coi

        class MyEnv1(gym.Env): ...

        class ProviderClass(coi.CustomPolicyProvider):
            @classmethod
            def get_policy_names(cls):
                return ["MyCustomPolicy-v1", ...]

            def load_policy(self, name):
                filename = ...
                return TD3.load(filename)

.. tab:: Entry points (setup.cfg)

   .. code-block:: cfg

        # setup.cfg

        [options.entry_points]
        cernml.envs =
            MyEnv-v1 = mypackage:MyEnv1
        cernml.custom_policies =
            MyEnv-v1 = mypackage:ProviderClass

   .. code-block:: py

        # mypackage/__init__.py

        import gym
        from cernml import coi

        class MyEnv1(gym.Env): ...

        class ProviderClass(coi.CustomPolicyProvider):
            @classmethod
            def get_policy_names(cls):
                return ["MyCustomPolicy-v1", ...]

            def load_policy(self, name):
                filename = ...
                return TD3.load(filename)

.. tab:: Entry points (setup.py)

   .. code-block:: py

        # setup.py

        from setuptools import setup

        # ...

        setup(
            # ...,
            entry_points={
                "cernml.envs": [
                    "MyEnv-v1 = mypackage:MyEnv1",
                ],
                "cernml.custom_policies": [
                    "MyEnv-v1 = mypackage:ProviderClass",
                ],
            },
        )

   .. code-block:: py

        # mypackage/__init__.py

        import gym
        from cernml import coi

        class MyEnv1(gym.Env): ...

        class ProviderClass(coi.CustomPolicyProvider):
            @classmethod
            def get_policy_names(cls):
                return ["MyCustomPolicy-v1", ...]

            def load_policy(self, name):
                filename = ...
                return TD3.load(filename)

.. tab:: Inheritance

   .. code-block:: py

        # mypackage/__init__.py

        import gym
        from cernml import coi

        class MyEnv1(gym.Env, coi.CustomPolicyProvider):

            # ...

            @classmethod
            def get_policy_names(cls):
                return ["MyCustomPolicy-v1", ...]

            def load_policy(self, name):
                filename = ...
                return TD3.load(filename)

        coi.register("MyEnv-v1", entry_point=MyEnv1)
