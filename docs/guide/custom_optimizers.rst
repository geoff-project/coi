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
