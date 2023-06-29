<!--
SPDX-FileCopyrightText: 2020-2023 CERN
SPDX-FileCopyrightText: 2023 GSI Helmholtzzentrum für Schwerionenforschung
SPDX-FileNotice: All rights not expressly granted are reserved.

SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+
-->

Common Optimization Interfaces
==============================

CernML is the project of bringing numerical optimization, machine learning and
reinforcement learning to the operation of the CERN accelerator complex.

CernML-COI defines common interfaces that facilitate using numerical
optimization and reinforcement learning (RL) on the same optimization problems.
This makes it possible to unify both approaches into a generic optimization
application in the CERN Control Center.

This repository can be found online on CERN's [Gitlab][].

[Gitlab]: https://gitlab.cern.ch/geoff/cernml-coi/

Table of Contents
-----------------

[[_TOC_]]

Motivation
----------

Several problems in accelerator control can be solved both using reinforcement
learning (RL) and numerical optimization. However, both approaches usually
slightly differ in their expected input and output:

- Optimizers pick certain *points* in the phase space of modifiable parameters
  and evaluate the loss of these parameters. They minimize this loss through
  multiple evaluations and ultimately yield the optimal parameters.
- RL agents assume that the problem has a certain state, which usually contains
  the values of all modifiable parameters. They receive an observation (which
  is usually higher-dimensional than the loss) and calculate a *correction* of
  the parameters. This correction yields a certain reward to them. Their goal
  is to optimize the parameters incrementally by optimzing their corrections
  for maximal *cumulative* reward.

More informally, optimizers start from scratch each time they are applied and
they yield a point in phase space. RL agents learn once, can be applied many
times, and they yield a sequence of deltas in the phase space.

Even more informally, on a given machine, an optimizer performs the state
transition `machine.parameters = new_parameters`, whereas an RL agent performs
the state transition `machine.parameters += corrections` iteratively.

This package provides interfaces to implement for problems that should be
compatible both with numerical optimizers and RL agents. It is based on the
[Gym][] environment API and enhances it with the `SingleOptimizable` interface.

In addition, the output and metadata of the environments is *restricted* to
make the behavior of environments more uniform and compatible to make them more
easily visualizable and integrable into a generic machine-optimization
application.

[Gym]: https://github.com/openai/gym/

Quickstart
----------

Start a Python project. In your `setup.cfg` or `setup.py`, add dependencies on
Gym and the COI. Make sure to pick a COI version that is supported by the
application that will optimize your problem.

```conf
# setup.cfg
[options]
install_requires =
    gym >= 0.11
    cernml-coi >= 0.8.0
```

Then, write a class that implements one or multiple of the optimization
interfaces. Finally *register* it so that an application that imports your
package may find it. (See the [Parabola example](/examples/parabola.py) for a
more fully featured version of the code below.)

```python
# my_project/__init__.py
import gym
import numpy as np
from cernml import coi

class Parabola(coi.SingleOptimizable, gym.Env):
    observation_space = gym.spaces.Box(-2.0, 2.0, shape=(2,))
    action_space = gym.spaces.Box(-1.0, 1.0, shape=(2,))
    optimization_space = gym.spaces.Box(-2.0, 2.0, shape=(2,))
    metadata = {
        "render.modes": [],
        "cern.machine": coi.Machine.NO_MACHINE,
    }

    def __init__(self):
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
```

Any [*host application*][GeOFF] may then import your package and instantiate
your optimization problem.

```python
import my_project
from cernml import coi

problem = coi.make("Parabola-v0")
optimize_in_some_way(problem)
```

[GeOFF]: https://gitlab.cern.ch/geoff/geoff-app

Stability
---------

This package uses a variant of [Semantic Versioning](https://semver.org/) that
makes additional promises during the initial development (major version 0):
whenever breaking changes to the public API are published, the first non-zero
version number will increase. This means that code that uses COI version 0.6.0
will continue to work with version 0.6.1, but may break with version 0.7.0.

Changelog
---------

[See here](https://cernml-coi.docs.cern.ch/changelog.html).

Documentation
-------------

Inside the CERN network, you can read the package documentation on the [Acc-Py
documentation server][acc-py-docs]. [The same documentation is available
outside of CERN][pages-docs] via CERN's [Gitlab Pages][pages-howto] service,
though some cross-links to CERN-internal projects may not work. Finally, API
documentation is provided through extensive Python docstrings.

[acc-py-docs]: https://acc-py.web.cern.ch/gitlab/geoff/cernml-coi/
[pages-docs]: https://cernml-coi.docs.cern.ch/
[pages-howto]: https://how-to.docs.cern.ch/

License
-------

Except as otherwise noted, this work is licensed under either of [GNU Public
License, Version 3.0 or later](LICENSES/GPL-3.0-or-later.txt), or [European
Union Public License, Version 1.2 or later](LICENSES/EUPL-1.2.txt), at your
option. See [COPYING](COPYING) for details.

Unless You explicitly state otherwise, any contribution intentionally submitted
by You for inclusion in this Work (the Covered Work) shall be dual-licensed as
above, without any additional terms or conditions.

For full authorship information, see the version control history.
