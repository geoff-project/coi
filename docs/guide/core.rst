..
    SPDX-FileCopyrightText: 2020-2024 CERN
    SPDX-FileCopyrightText: 2023-2024 GSI Helmholtzzentrum für Schwerionenforschung
    SPDX-FileNotice: All rights not expressly granted are reserved.

    SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

The Core API
============

.. digraph:: inheritance_diagram
    :caption: "Fig. 1: Inheritance diagram of the core interfaces"

    rankdir = "BT";
    bgcolor = "#00000000";
    node [shape=record, fontname="Latin Modern Sans", style=filled, fillcolor="white"];
    edge [style=dashed];

    problem[label=<{
        cernml.coi.<b>Problem</b>|
        render(<i>mode</i>: str) → Any<br/>close() → None|
        <i>metadata</i>: Dict[str, Any]<br/><i>unwrapped</i>: Problem}>,
    ];

    sopt[label=<{
        cernml.coi.<b>SingleOptimizable</b>|
        get_initial_params() → Params<br/>compute_single_objective(<i>p</i>: Params) → float|
        <i>optimization_space</i><br/><i>objective_range</i><br/><i>constraints</i>}>,
    ];

    env[label=<{
        gym.<b>Env</b>|
        reset() → Obs<br/>step(<i>a</i>: Action) → Obs, …<br/>seed(…) → …|
        <i>action_space</i><br/><i>observation_space</i><br/><i>reward_range</i>}>,
    ];

    optenv[label=<cernml.coi.<b>OptEnv</b>>];

    optenv -> sopt -> problem;
    optenv -> env -> problem;

The interfaces are designed in a modular fashion: depending on the algorithms
that an optimization problem supports, it either implements
`~cernml.coi.SingleOptimizable` (for classical single-objective optimization),
`~gym.Env` (for reinforcement learning) or both. The `~cernml.coi.Problem`
interface captures the greatest common denominator – that, which all interfaces
have in common.

As a convenience, this package also provides the `~cernml.coi.OptEnv`
interface. It is simply an intersection of `~cernml.coi.SingleOptimizable` and
`~gym.Env`. This means that implementing it is the same as implementing both of
its bases. At the same time, every class that implements both base interfaces
also implements `~cernml.coi.OptEnv`. A demonstration:


.. code-block:: python

    import gymnasium as gym
    from cernml import coi

    class Indirect(coi.SingleOptimizable, gym.Env):
        ...

    assert issubclass(Indirect, coi.OptEnv)


Metadata
--------

Every optimization problem should have a class attribute called
`~cernml.coi.Problem.metadata`, which is a dict with string keys. The
dict must be defined at the class level and immutable. It communicates
fundamental properties of the class and how a host application can use it.

The following keys are defined and understood by this package:

``"render_modes"``
    the render modes that the optimization problem understands (see
    :ref:`Rendering`);

``"cern.machine"``
    the accelerator that an optimization problem is associated with;

``"cern.japc"``
    a boolean flag indicating whether the problem's constructor expects an
    argument named *japc* of type :class:`~japc:pyjapc.PyJapc`;

``"cern.cancellable"``
    A boolean flag indicating whether the problem's constructor expects an
    argument named *cancellation_token* of type `cancellation.Token
    <cernml.coi.cancellation.Token>` (see :ref:`Cancellation`).

See the :attr:`API docs<cernml.coi.Problem.metadata>` for a full spec.

Rendering
---------

The metadata entry ``"render_modes"`` allows a problem to declare that its
internal state can be visualized. It should be a list of strings where each
string is a supported render mode. Host applications may pick one of these
strings and pass it to the problems {meth}`~cernml.coi.Problem.render()`
method. For this to work, render modes need to have well-defined semantics.

The following render modes are standardized by either Gym or this package:

``"human"``
    The default mode, for interactive use. This should e.g. open a window and
    display the problem's current state in it. Displaying the window should not
    block control flow.

``"ansi"``
    Return a text-only representation of the problem. This may contain e.g.
    terminal control codes for color effects.

``"rgb_array"``
    Return a Numpy array representing color image data.

``"matplotlib_figures"``
    Return a list of Matplotlib :class:`~matplotlib.figure.Figure` objects,
    suitable for embedding into a GUI application.

See the `~cernml.coi.Problem.render()` docs for a full spec of each render
mode.

Naming Your Quantities
----------------------

In many cases, your objective function and parameters directly correspond to
machine parameters. For example, many optimization problems might only scale
their parameters and otherwise send them unmodified to the machine via JAPC.
Similarly, the objective function might only be a rescaled or inverted reading
from a detector on the accelerator.

In such cases, it is useful to declare the meaning of your quantities. A host
application may use this to annotate its graphs of the parameters and objective
function. The `~cernml.coi.SingleOptimizable` class provides three attributes
for this purpose:

.. code-block:: python

    from cernml import coi

    class SomeProblem(coi.SingleOptimizable):

        objective_name = "RMS BPM Position (mm)"
        param_names = [
            "CORRECTOR.10",
            "CORRECTOR.20",
            "CORRECTOR.30",
            "CORRECTOR.40",
        ]
        constraint_names = [
            "BCT Intensity",
        ]

        def compute_single_objective(self, params):
            for name, value in zip(self.param_names, params):
                self._japc.setParam(f"logical.{name}/K", value)
            ...

Note that these three values need not be defined inside the class scope. You
are free to define them inside your ``__init__()`` method or change them at
run-time. This is useful because some optimization problems might decide to be
configurable in the exact devices they talk to.

You are free not to define these attributes at all. In this case, the host
application will see the inherited default values and assume no particular
meaning of your quantities.

Closing
-------

Some optimization problems have to acquire certain resources in order to
perform their tasks. Examples include:

- spawning processes,
- starting threads,
- subscribing to JAPC parameters.

While Python garbage-collects objects which are no longer accessible (including
`~cernml.coi.Problem` instances), some of these resources require manual
function calls in order to be properly cleaned up.

If such is the case for an optimization problem, it should override the
`~cernml.coi.Problem.close()` method and define all such actions in it. A host
application is required to call `~cernml.coi.Problem.close()` when it has no more
need for an optimization problem.

.. warning::
    The `~cernml.coi.Problem.close()` method is *not* called after an
    optimization procedure is done. In particular, a host application may
    perform several optimization runs on the same problem and call
    `~cernml.coi.Problem.close()` only at the very end. Furthermore, an
    arbitrary amount of time may pass between the last call to
    `~cernml.coi.SingleOptimizable.compute_single_objective()` and the call to
    `~cernml.coi.Problem.close()`.

.. note::
    If you want to use an optimization problem in your own application or
    script, consider using the :func:`~contextlib.closing()` context manager:

    .. code-block:: python

        from contextlib import closing

        with closing(MyProblem(...)) as problem:
            optimize(problem)

    The context manager ensures that `~cernml.coi.Problem.close()` is called
    under all circumstances – even if an exception occurs.

Spaces
------

Optimization is always executed over a certain numeric *domain*, i.e. a space
of allowed values. These domains are encapsulated by Gym's concept of a
`~gym.spaces.Space`. While Gym provides many different kinds of spaces
(discrete, continuous, aggregate, …), this package for now only supports
`~gym.spaces.Box` for maximum portability. This restriction may be lifted in
the future.

In addition, box spaces are for now restricted to the bounds [−1; +1]. This
restriction, too, may be lifted in the future.

The interfaces make use of spaces as follows:

`SingleOptimizable.optimization_space<cernml.coi.SingleOptimizable.optimization_space>`
    the domain of valid inputs to
    `~cernml.coi.SingleOptimizable.compute_single_objective()`;

`Env.action_space<gym.Env>`
    the domain of valid inputs to `~gym.Env.step()`;

`Env.observation_space<gym.Env>`
    the domain of valid observations returned by `~gym.Env.reset()` and
    `~gym.Env.step()`.

Control Flow for ``SingleOptimizable``
--------------------------------------

The `~cernml.coi.SingleOptimizable` interface provides two methods that a host
application can interact with:
`~cernml.coi.SingleOptimizable.get_initial_params()` and
`~cernml.coi.SingleOptimizable.compute_single_objective()`.

The `~cernml.coi.SingleOptimizable.get_initial_params()` method should return a
reasonable point in phase space from where to start optimization. E.g. this may
be the current state of the machine; a constant, known-good point; or a
randomly-chosen point in phase space.

It must always be safe to call
`~cernml.coi.SingleOptimizable.compute_single_objective()` directly with the
result of `~cernml.coi.SingleOptimizable.get_initial_params()`. Afterwards, an
optimizer may choose any point in the phase space defined by the
`~cernml.coi.SingleOptimizable.optimization_space` and pass it to
`~cernml.coi.SingleOptimizable.compute_single_objective()`. This will typically
happen in a loop until the optimizer has found a minimum of the objective
function.

Even after optimization is completed, a host application may call
`~cernml.coi.SingleOptimizable.compute_single_objective()` again with the value
returned by `~cernml.coi.SingleOptimizable.get_initial_params()` before
optimization. A use case is that optimization has failed and the user wishes to
reset the machine to the state before optimization.

In addition, this basic control flow can be interleaved arbitrarily with calls
to `~cernml.coi.Problem.render()` in order to visualize progress to the user.

Thus, typical control flow looks as follows:

.. code-block:: python

    from cernml import coi

    show_progress: bool = ...
    optimizer = ...
    problem = coi.make("MySingleOptimizableProblem-v0")
    initial = params = problem.get_initial_params()

    while not optimizer.is_done():
        loss = problem.compute_single_objective(params)
        params = optimizer.step(loss)
        if show_progress:
            problem.render(...)

    if optimizer.has_failed():
        problem.compute_single_objective(initial)

Control Flow for ``Env``
------------------------

The `~gym.Env` interface provides three methods that a host application can
interact with: `~gym.Env.reset()`, `~gym.Env.step()` and
`~cernml.coi.Problem.close()`. In contrast to `~cernml.coi.SingleOptimizable`,
the `~gym.Env` interface is typically called many times in *episodes*,
especially during training. Each episode follows the same protocol.

The `~gym.Env.reset()` method is called at the start of an episode. It
typically picks a random, known-bad initial state and clears any state from the
previous episode. It eventually must return an initial observation to seed the
agent. Though an environment may pick a constant initial state or re-use the
current state, (see :ref:`the above section <Control Flow for
\`\`SingleOptimizable\`\`>`), this is often reduces the amount of experience a
reinforcement learner can gather.

Afterwards, the host application calls an agent to decide on an action given
the current observation. This action is then passed to `~gym.Env.step()`, which
must return a 4-tuple of the following values:

*obs*
    the next observation after the action has been applied;

*reward*
    the reward for the given action (a reinforcement learner's goal is to
    maximize the expected cumulative reward over an episode);

*done*
    a boolean flag indicating whether the episode has ended;

*info*
    a dict mapping from strings to arbitrary values.

This is done in a loop until the episode is ended by passing a True value as
*done*. Once the episode is over, the host application will make no further
call to `~gym.Env.step()` until the next episode is started via
`~gym.Env.reset()`. A host application is also free to end an episode
prematurely, e.g. to call `~gym.Env.reset()` before an episode is over. There
is no guarantee that any episode is ever driven to completion.

The *info* dict is free to return any additional information. There is
currently only one standardized key:

``"success"``
    a bool indicating whether the episode has ended by reaching a "good"
    terminal state. Absence of this key may either mean that the episode hasn't
    ended, that a "bad" terminal state has been reached, or that there is not
    difference between terminal states.

The `~cernml.coi.Problem.close()` method is called at the end of the lifetime
of an environment. No further calls to the environment will be made afterwards.
It should use this method to release any resources it has acquired in its
constructor.

In addition, this basic control flow can be interleaved arbitrarily with calls
to `~cernml.coi.Problem.render()` in order to visualize progress to the user.

Thus, typical control flow looks as follows:

.. code-block:: python

    from cernml import coi
    from contextlib import closing
    from gym.wrappers import TimeLimit

    show_progress: bool = ...
    num_episodes: int = ...
    agent = ...

    # Use TimeLimit to prevent infinite loops.
    env = TimeLimit(coi.make("MyEnv-v0"), 10)

    with closing(env):
        for _ in range(num_episodes):
            done = False
            obs = env.reset()
            while not done:
                action = agent.predict(obs)
                obs, reward, done, info = env.step(action)
                if show_progress:
                    env.render(...)
                    display(reward, info, ...)

Additional Restrictions
-----------------------

For maximum compatibility, this API puts the following *additional*
restrictions on environments:

- The `observation_space<gym.Env>`, `action_space<gym.Env>` and
  `~cernml.coi.SingleOptimizable.optimization_space` must all be
  `Boxes<gym.spaces.Box>`. The only exception is if the environment is a
  `~gym.GoalEnv`: in that case, `observation_space<gym.Env>` must be
  `gym.spaces.Dict` (with exactly the three expected keys) and the
  ``"observation"`` sub-space must be a `gym.spaces.Box`.
- The `action_space<gym.Env>` and the
  `~cernml.coi.SingleOptimizable.optimization_space`  must have the same shape;
  They must only differ in their bounds. The bounds of the action space must be
  symmetric around zero and normalized (equal to or less than one).
- If the environment supports any rendering at all, it should support at least
  the *human*, *ansi* and *matplotlib_figures*. The former two facilitate
  debugging and stand-alone usage, the latter makes it possible to embed the
  environment into a GUI.
- The environment metadata must contain a key ``cern.machine`` with a value of
  type `~cernml.coi.Machine`. It tells users which CERN accelerator the
  environment belongs to.
- Rewards must always lie within the defined reward range and objectives within
  the defined objective range. Both ranges are unbounded by default.
- The problems must never diverge to NaN or infinity.

For the convenience of problem authors, this package provides a function
`~cernml.coi.check()` that verifies these requirements on a best-effort basis.
If you package your problem, we recommend adding a unit test to your package
that calls this function and exercise it on every CI job. See the `Acc-Py
guidelines`_ on testing for more information.

.. _Acc-Py guidelines: https://wikis.cern.ch/display/ACCPY/Testing
