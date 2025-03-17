.. SPDX-FileCopyrightText: 2020 - 2024 CERN
.. SPDX-FileCopyrightText: 2023 - 2024 GSI Helmholtzzentrum für Schwerionenforschung
.. SPDX-FileNotice: All rights not expressly granted are reserved.
..
.. SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

Quickstart
==========

.. currentmodule:: cernml.coi

Start a Python project. In your manifest file, add a dependency on the COI.
Make sure to pick a COI version that is supported by the application that will
optimize your problem:

.. tab:: pyproject.toml

    .. code-block:: toml
        :linenos:
        :emphasize-lines: 9

        [build-system]
        requires = ['setuptools']
        build-backend = 'setuptools.build_meta'

        [project]
        name = 'my-project'
        version = '1.0'
        dependencies = [
            'cernml-coi >= 0.9.0',
        ]

.. tab:: setup.cfg

    .. code-block:: cfg
        :linenos:
        :emphasize-lines: 7

        [metadata]
        name = my-project
        version = 1.0

        [options]
        install_requires =
            cernml-coi >= 0.9.0

.. tab:: setup.py

    .. code-block:: python
        :linenos:
        :emphasize-lines: 7

        from setuptools import setup

        setup(
            name='my-project',
            version='1.0',
            install_requires=[
                'cernml-coi >= 0.9.0',
            ],
        )

Now consider the following optimization problem: It is defined by an *objective
function* and an *initial point*:

.. code-block:: python
    :caption: my_project/__init__.py
    :linenos:

    import numpy as np

    def objective_function(x):
        goal = np.array([0.123, -0.456])
        return np.linalg.norm(x - goal)

    x0 = np.zeros(2)


Now, write a class that implements multiple of the :doc:`optimization
interfaces <core>`, specifically interfaces for single-objective numerical
optimization and reinforcement learning.

.. code-block:: python
    :caption: my_project/__init__.py
    :lineno-start: 8

    import gymnasium as gym
    import numpy as np
    from cernml import coi

    class Parabola(coi.SingleOptimizable, gym.Env):
        metadata = {
            "render_modes": [],
            "cern.machine": coi.Machine.NO_MACHINE,
        }

        # Obervations for RL are 2D vectors in the box from -2 to +2.
        observation_space = gym.spaces.Box(-2.0, 2.0, shape=(2,))

        # RL agents may make steps that are 2D vectors from -1 to +1.
        action_space = gym.spaces.Box(-1.0, 1.0, shape=(2,))

        # Numerical optimization searches within a 2D box from -2 to +2.
        optimization_space = gym.spaces.Box(-2.0, 2.0, shape=(2,))

        def __init__(self, render_mode=None):
            super().__init__(render_mode)
            self.pos = x0.copy()

        # Single-objective optimization methods:

        def get_initial_params(self, *, seed=None, options=None):
            super().reset(seed=seed, options=options)
            self.pos = x0.copy()
            return self.pos.copy()

        def compute_single_objective(self, params):
            # Force parameters into observable space.
            space = self.optimization_space
            self.pos = np.clip(params, space.low, space.high)
            return objective_function(self.pos)

        # Reinforcement learning methods:

        def reset(self, *, seed=None, options=None):
            super().reset(seed=seed, options=options)
            self.pos = x0.copy()
            obs = self.pos.copy()
            info = {}
            return obs, info

        def step(self, action):
            space = self.observation_space
            self.pos = np.clip(self.pos + action, space.low, space.high)
            obs = self.pos.copy()
            reward = -objective_function(self.pos)
            terminated = (reward > -0.05)
            truncated = next_pos not in ob_space
            info = {}
            return obs, reward, terminated, truncated, info

    coi.register("Parabola-v0", entry_point=Parabola, max_episode_steps=10)

Do take note of that last statement, which :doc:`registers <registration>` your
class whenever your package is imported.

We still need to declare how to find our class. We put the entry point
:ep:`cernml.envs` into our manifest file for this:

.. tab:: pyproject.toml

    .. code-block:: toml
        :lineno-start: 10
        :emphasize-lines: 2

        [project.entry-points.'cernml.envs']
        my-project = 'my_project'

.. tab:: setup.cfg

    .. code-block:: cfg
        :lineno-start: 8
        :emphasize-lines: 3

        [entry_points]
        cernml.envs =
            my-project = my_project

.. tab:: setup.py

    .. code-block:: python
        :linenos:
        :emphasize-lines: 11

        from setuptools import setup

        setup(
            name='my-project',
            version='1.0',
            install_requires=[
                'cernml-coi >= 0.9.0',
            ],
            entry_points={
                'cernml.envs': [
                    'my-project = my_project',
                ],
            }
        )

Any *host application* (e.g. Geoff_) may now instantiate your optimization
problem by passing both the *namespace* of your entry point and the
*environment ID* of the register call. If you don't have a proper application
available, the package :doc:` cernml-coi-optimizers <optimizers:index>`
provides a simple optimization loop:

.. _Geoff: https://gitlab.cern.ch/geoff/geoff-app

.. code-block:: python
    :caption: solve_parabola.py
    :linenos:

    from cernml import coi, optimizers

    # Imports happens automatically behind the scene!
    env = coi.make("my-project/Parabola-v0")
    opt = optimizers.make("BOBYQA")

    # Uses the BOBYQA algorithm to solve our quadratic problem.
    optimizers.solve(opt, env)

Install Extras
--------------

This package defines the following :ref:`optional dependencies
<setuptools:keyword/extras_require>`. You can include them by adding the names
of all extras in a comma-separated list in brackets behind the name of this
package, e.g.:

.. code-block:: toml

    # pyproject.toml
    [project]
    dependencies = [
        'cernml-coi[matplotlib, optimizers] >= 0.8.0',
    ]

.. extra:: matplotlib
    :no-index:

    Adds a dependency on :doc:`matplotlib <mpl:index>`. This is used by a few
    :doc:`/api/checkers`.

.. extra:: optimizers
    :no-index:

    Adds a dependency on :doc:`cernml-coi-optimizers <optimizers:index>`. This
    is only used for the type annotations of `CustomOptimizerProvider`.

.. extra:: robotics
    :no-index:

    Adds a dependency on :doc:`gymnasium-robotics <gymrob:index>`. We extend
    the :ref:`guide/otherenvs:multi-goal environments` that it defines. But if
    this package isn't installed, we poly-fill
    `~gymnasium_robotics.core.GoalEnv` with our own implementation.

.. extra:: all
    :no-index:

    Adds all optional dependencies *except* the one on gymnasium-robotics. This
    exists mostly for convenience.

For easier maintenance, this package also defines the following extras:

.. extra:: doc
    :no-index:

    Adds all dependencies necessary to build the documentation for this
    package.

.. extra:: examples
    :no-index:

    Adds all dependencies necessary to run the :doc:`/examples/index` provided
    by this package.

.. extra:: test
    :no-index:

    Adds all dependencies to run the unit tests defined for this package.
