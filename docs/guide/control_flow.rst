..
    SPDX-FileCopyrightText: 2020-2024 CERN
    SPDX-FileCopyrightText: 2023-2024 GSI Helmholtzzentrum für Schwerionenforschung
    SPDX-FileNotice: All rights not expressly granted are reserved.

    SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

Control Flow of Optimization Problems
=====================================

.. currentmodule:: cernml.coi

This page describes the order in which the functions of the various interfaces
are expected to be called. This is sometimes also called the *lifecycle* of an
object.

The contract describes here binds both parties: host applications are expected
not to call functions out of the expected order; and plugins are expected to be
prepared to handle calls that are unusual but within these guidelines.

Control Flow for ``SingleOptimizable``
--------------------------------------

The `SingleOptimizable` interface provides two methods that a host application
can interact with: `~SingleOptimizable.get_initial_params()` and
`~SingleOptimizable.compute_single_objective()`.

The `~SingleOptimizable.get_initial_params()` method should return a reasonable
point in phase space from where to start optimization. E.g. this may be the
current state of the machine; a constant, known-good point; or
a randomly-chosen point in phase space.

It must always be safe to call `~SingleOptimizable.compute_single_objective()`
directly with the result of `~SingleOptimizable.get_initial_params()`.
Afterwards, an optimizer may choose any point in the phase space defined by the
`~SingleOptimizable.optimization_space` and pass it to
`~SingleOptimizable.compute_single_objective()`. This will typically happen in
a loop until the optimizer has found a minimum of the objective function.

Even after optimization is completed, a host application may call
`~SingleOptimizable.compute_single_objective()` again with the value returned
by `~SingleOptimizable.get_initial_params()` before optimization. A use case is
that optimization has failed and the user wishes to reset the machine to the
state before optimization.

In addition, this basic control flow can be interleaved arbitrarily with calls
to `~Problem.render()` in order to visualize progress to the user.

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

The `Env` interface provides three methods that a host application can interact
with: :func:`~gymnasium.Env.reset()`, :func:`~gymnasium.Env.step()` and
`~Problem.close()`. In contrast to `SingleOptimizable`, the `Env` interface is
typically called many times in *episodes*, especially during training. Each
episode follows the same protocol.

The :func:`~gymnasium.Env.reset()` method is called at the start of an episode.
It typically picks a random, known-bad initial state and clears any state from
the previous episode. It eventually must return an initial observation to seed
the agent. Though an environment may pick a constant initial state or re-use
the current state, (see :ref:`the above section <guide/control_flow:Control
Flow for \`\`SingleOptimizable\`\`>`), this is often reduces the amount of
experience a reinforcement learner can gather.

Afterwards, the host application calls an agent to decide on an action given
the current observation. This action is then passed to
:func:`~gymnasium.Env.step()`, which must return a 5-tuple of the following
values:

*obs*
    the next observation after the action has been applied;

*reward*
    the reward for the given action (a reinforcement learner's goal is to
    maximize the expected cumulative reward over an episode);

*terminated*
    a boolean flag indicating whether the agent has reached a terminal state of
    the environment (e.g. game won/lost).

*truncated*
    a boolean flag indicating whether the episode has been ended due to
    a reason external to the environment (e.g. training time limit expired).

*info*
    a dict mapping from strings to arbitrary values.

This is done in a loop until the episode is ended by passing a True value for
either of *terminated* or *truncated* (or both). Once the episode is over, the
host application will make no further call to :func:`~gymnasium.Env.step()`
until the next episode is started via :func:`~gymnasium.Env.reset()`. A host
application is also free to end an episode prematurely, e.g. to call
:func:`~gymnasium.Env.reset()` before an episode is over (though doing so
during training would be bad for the trained agent). There is no guarantee that
any episode is ever driven to completion.

The *info* dict is free to return any additional information. There is
currently only one standardized key:

``"success"``
    a bool indicating whether the episode has ended by reaching a "good"
    terminal state. Absence of this key may either mean that the episode hasn't
    ended, that a "bad" terminal state has been reached, or that there is not
    difference between terminal states.

The `~Problem.close()` method is called at the end of the lifetime of an
environment. No further calls to the environment will be made afterwards. It
should use this method to release any resources it has acquired in its
constructor.

In addition, this basic control flow can be interleaved arbitrarily with calls
to `~Problem.render()` in order to visualize progress to the user.

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
