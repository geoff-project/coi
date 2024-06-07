..
    SPDX-FileCopyrightText: 2020-2024 CERN
    SPDX-FileCopyrightText: 2023-2024 GSI Helmholtzzentrum für Schwerionenforschung
    SPDX-FileNotice: All rights not expressly granted are reserved.

    SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

Quickstart
==========

.. currentmodule:: cernml.coi

Start a Python project. In your manifest file, add dependencies on
:doc:`Gymnasium <gym:index>` and the COI. Make sure to pick a COI version that
is supported by the application that will optimize your problem:

.. tab:: pyproject.toml

    .. code-block:: toml

        [project]
        dependencies = [
            'gymnasium > 0.29',
            'cernml-coi >= 0.8.0',
        ]

.. tab:: setup.cfg

    .. code-block:: cfg

        [options]
        install_requires =
            gymnasium >= 0.29
            cernml-coi >= 0.8.0

.. tab:: setup.py

    .. code-block:: python

        from setuptools import setup

        setup(
            # ...,
            install_requires=[
                'gymnasium >= 0.29',
                'cernml-coi >= 0.8.0',
            ],
        )

Then, write a class that implements one or multiple of the :doc:`optimization
interfaces <core>`. Finally :doc:`register <registration>` it so that an
application that imports your package may find it. See the
:doc:`/examples/parabola` for a more fully featured version of the code below.

.. code-block:: python
    :linenos:

    # my_project/__init__.py
    import gymnasium as gym
    import numpy as np
    from cernml import coi

    class Parabola(coi.SingleOptimizable, gym.Env):
        observation_space = gym.spaces.Box(-2.0, 2.0, shape=(2,))
        action_space = gym.spaces.Box(-1.0, 1.0, shape=(2,))
        optimization_space = gym.spaces.Box(-2.0, 2.0, shape=(2,))
        metadata = {
            "render_modes": [],
            "cern.machine": coi.Machine.NO_MACHINE,
        }

        def __init__(self, render_mode=None):
            self.render_mode = render_mode
            self.pos = np.zeros(2)
            self._train = True

        def reset(self):
            self.pos = self.action_space.sample()
            return self.pos.copy()

        def step(self, action):
            next_pos = self.pos + action
            ob_space = self.observation_space
            self.pos = np.clip(next_pos, ob_space.low, ob_space.high)
            reward = -sum(self.pos ** 2)
            done = (reward > -0.05) or next_pos not in ob_space
            return self.pos.copy(), reward, done, {}

        def get_initial_params(self):
            return self.reset()

        def compute_single_objective(self, params):
            ob_space = self.observation_space
            self.pos = np.clip(params, ob_space.low, ob_space.high)
            loss = sum(self.pos ** 2)
            return loss

    coi.register("Parabola-v0", entry_point=Parabola, max_episode_steps=10)

Any *host application* (e.g. Geoff_) may then import your package and
instantiate your optimization problem.

.. code-block:: python

    import my_project
    from cernml import coi

    problem = coi.make("Parabola-v0")
    optimize_in_some_way(problem)

.. _Geoff: https://gitlab.cern.ch/geoff/geoff-app

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
