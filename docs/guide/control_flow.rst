.. SPDX-FileCopyrightText: 2020 - 2025 CERN
.. SPDX-FileCopyrightText: 2023 - 2025 GSI Helmholtzzentrum für Schwerionenforschung
.. SPDX-FileNotice: All rights not expressly granted are reserved.
..
.. SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

:tocdepth: 3

Control Flow of Optimization Problems
=====================================

.. seealso::
   :ref:`guide/core:Running Your Optimization Problem`
        A much shorter overview focused on minimal examples.

.. currentmodule:: cernml.coi

This page describes the order in which the functions of the various interfaces
are expected to be called. This is sometimes also called the *lifecycle* of an
object.

The contract describes here binds both parties: host applications are expected
not to call functions out of the expected order; and plugins are expected to be
prepared to handle calls that are unusual but within these guidelines.

Control Flow for SingleOptimizable
----------------------------------

The `SingleOptimizable` interface provides two methods that a host application
can interact with: `~SingleOptimizable.get_initial_params()` and
`~SingleOptimizable.compute_single_objective()`.

The Execution Loop
^^^^^^^^^^^^^^^^^^

A host application **must receive an initial point** by calling
`~SingleOptimizable.get_initial_params()` before any call to
`~SingleOptimizable.compute_single_objective()`. The initial point usually
seeds the optimization algorithm. It is often the current state of the system,
a fixed reasonable guess, or a random point in the phase space.

Once the initial point has been received, host applications may call
`~SingleOptimizable.compute_single_objective()` as many times as desired.
Arguments to the function **must lie within the bounds** of the
`~SingleOptimizable.optimization_space`. Optimization algorithms are strongly
encouraged to **use the initial point as argument to their first call** to
`~SingleOptimizable.compute_single_objective()`.

Host algorithms should not assume that **the last evaluation** of an
optimization algorithm is also the optimal one. After a successful
optimization, they should call `~SingleOptimizable.compute_single_objective()`
once more with the optimal argument. Because `SingleOptimizable` objects are
stateful, this is expected to set them to their optimal state.

The Initial Point
^^^^^^^^^^^^^^^^^

.. TODO: It's unclear what to do if the initial point is out of bounds.
    https://gitlab.cern.ch/geoff/cernml-coi/-/issues/3

The initial point is strongly encouraged to **lie within bounds** of the
`~SingleOptimizable.optimization_space`. Host applications may assume that it's
safe to call `~SingleOptimizable.compute_single_objective()` with the point
returned by `~SingleOptimizable.get_initial_params()`. This often happens when
an optimization has failed or been cancelled and a user wishes to return the
system to its initial state.

This implies that `~SingleOptimizable.compute_single_objective()` **should not
clip its argument** into bounds. Instead, host applications are strongly
encouraged to clip them before calling
`~SingleOptimizable.compute_single_objective()`, and to **never clip the
result** of `~SingleOptimizable.get_initial_params()`.

Cancellation and Repetition
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Optimization runs **may be cancelled** at any point. A `SingleOptimizable` may
not expect to run to completion every time. In particular, a user may want to
interrupt a call to `~SingleOptimizable.compute_single_objective()` if it takes
a considerable time. Optimization problems are encouraged to use
:ref:`guide/cancellation:cancellation` to honor such requests.

A host application may call `~SingleOptimizable.get_initial_params()` **more
than once**. Each call to the function is expected to start a new optimization,
so `SingleOptimizable` is allowed to clear internal buffers and restart any
rendering from scratch.

Rendering
^^^^^^^^^

Host applications may call `~Problem.render()` at any point between other
calls, including **before the first call** to
`~SingleOptimizable.get_initial_params()`. Rendering may be requested multiple
times between two calls to `~SingleOptimizable.compute_single_objective()`, so
it should not modify the state of the problem.

Calls to `~SingleOptimizable.get_initial_params()` and
`~SingleOptimizable.compute_single_objective()` should not automatically call
`~Problem.render()` except when:

- the render mode is :rmode:`"human"`;
- the render mode is list-based, e.g. :rmode:`"rgb_array_list"` or
  :rmode:`"ansi_list"`.

SingleOptimizable Example
^^^^^^^^^^^^^^^^^^^^^^^^^

A typical execution loop could look like this:

.. literalinclude:: minimal_sopt_loop.py
    :lines: 13-
    :linenos:

Control Flow for FunctionOptimizable
------------------------------------

Though the `FunctionOptimizable` is similar to a sequence of multiple
:ref:`single-objective optimization problems <guide/control_flow:Control Flow
for SingleOptimizable>`, *much* greater care must be taken around correctly
resetting them in case of failure.

Skeleton Points
^^^^^^^^^^^^^^^

The precise meaning of the time parameter is a little vague, since it will
typically depend on the institution and context where it is used.

In the `CERN accelerator complex`_, the injectors such as PS_ and SPS_ run in
*cycles* where each cycle is one full sequence of particle injection,
acceleration, and extraction (with several optional stages in between). Each
cycle is typically associated with a different *user*, who may request the beam
to go down a particular path of the complex (e.g. towards the LHC_ or towards
the `North Experimental Area`_).

.. _CERN accelerator complex: https://home.cern/science/accelerator-complex
.. _PS: https://home.cern/science/accelerators/proton-synchrotron
.. _SPS: https://home.cern/science/accelerators/super-proton-synchrotron
.. _LHC: https://home.cern/science/accelerators/large-hadron-collider
.. _North Experimental Area: https://home.cern/science/experiments

In this context, the skeleton points are points in time along one cycle given
in milliseconds. They're always measured from the start of the cycle (rather
than e.g. from the start of injection).

.. warning::
    Other laboratories are strongly encouraged to adopt a similarly strong
    notion about the interpretation of skeleton points. To facilitate
    cooperation and to **avoid catastrophic human error**, the notion of
    skeleton points should be as homogeneous across a laboratory as possible.

Selecting Skeleton Points
^^^^^^^^^^^^^^^^^^^^^^^^^

A host application must **query skeleton points** from the optimization problem
via `~FunctionOptimizable.override_skeleton_points()`. If it returns a list,
**that list of points must be used** in the following optimization. If (and
only if) it returns None, the user may be prompted to input a list of their
choosing. Whether `~FunctionOptimizable.override_skeleton_points()` returns
a list or None may depend on its configuration.

Sequencing Optimizations
^^^^^^^^^^^^^^^^^^^^^^^^

Optimizations of individual skeleton points are **always fully sequenced with
respect to each other**. Only once a skeleton point has been fully optimized
may the next optimization be started. Optimization problems are allowed to
allocated resources based on whether the skeleton point parameter has changed.

Skeleton points are always optimized **in order, from lowest to highest**.
Optimization problems may rely on this fact and e.g. use the fact that
`~FunctionOptimizable.get_initial_params()` has been called with a lower
skeleton point than before as a signal to clear their rendering data.

This sequencing rule includes `~FunctionOptimizable.get_optimization_space()`
and `~FunctionOptimizable.get_initial_params()`: the methods may only be called
with a skeleton point **once the optimization for that point starts**. It is
forbidden to e.g. fetch the spaces or the initial parameters for all skeleton
points at once and then start optimization for each of them.

Resetting
^^^^^^^^^

Within the optimization of a single skeleton point, the same :ref:`rules as for
SingleOptimizable apply <guide/control_flow:the execution loop>`. One exception
concerns cancellation of an optimization due to an error or user request. When
a `FunctionOptimizable` is reset, the reset must begin with the lowest
skeleton point and then proceed to the highest that the host application has
interacted with. **Skeleton points higher than the one whose optimization was
interrupted must not be reset.** This means that host applications must usually
keep track of which skeleton points have been optimized and which haven't.

FunctionOptimizable Example
^^^^^^^^^^^^^^^^^^^^^^^^^^^

A typical execution loop over multiple skeleton points could look like this:

.. literalinclude:: minimal_fopt_loop.py
    :lines: 17-
    :linenos:

Control Flow for Env
--------------------

The `Env` interface provides three methods that a host application can interact
with: :func:`~gymnasium.Env.reset()`, :func:`~gymnasium.Env.step()` and
`~Problem.close()`. In contrast to `SingleOptimizable`, the `Env` interface is
typically called many times in *episodes*, especially during training. Each
episode follows the same protocol.

Episode Start
^^^^^^^^^^^^^

The :func:`~gymnasium.Env.reset()` method **must be called at the start of an
episode**. It may clear any buffers from the previous episode and set the
system to an initial state. That state may be constant, but is typically random
and known to be bad. The function then returns an **initial observation** that
is used to seed the RL agent. It also returns :ref:`an info
dict<guide/control_flow:the info dict>`, which may contain additional debugging
information or other metadata.

.. note::
    The `~gymnasium.wrappers.AutoResetWrapper` calls
    :func:`~gymnasium.Env.reset()` automatically, even if a host application
    doesn't do so.

Episode Steps
^^^^^^^^^^^^^

The *initial observation* given by :func:`~gymnasium.Env.reset()` is passed to
the RL agent, which calculates a recommended *action* based on its *policy*.
This action is passed to :func:`~gymnasium.Env.step()`, which must return
a quintuple :samp:`({obs}, {reward}, {terminated}, {truncated}, {info})`,
where:

*obs*
    is the **next observation** and must be used to determine the next action;

*reward*
    is the reward for the previous action (a reinforcement learner's **goal is
    to maximize** the expected cumulative reward over an episode);

*terminated*
    is a boolean flag indicating whether the agent has reached a **terminal
    state** of the environment (e.g. game won/lost);

*truncated*
    is a boolean flag indicating whether the episode has been ended due to
    a **reason external to the environment** (e.g. training time limit
    expired).

*info*
    is :ref:`an info dict<guide/control_flow:the info dict>`, which may contain
    additional debugging information or other metadata.

In short: given the initial observation, agent and environment act in a loop,
with observations going into the agent and actions into the environment, until
the end of the episode.

**An episode ends** when the return value of either *terminated* or *truncated*
(or both) is True. When the episode is over, the host application must not make
any further calls to :func:`~gymnasium.Env.step()`. Instead, it must call
:func:`~gymnasium.Env.reset()` to start the next episode.

The host application is free to **end an episode prematurely**, i.e. to call
:func:`~gymnasium.Env.reset()` before the end of the episode. There is no
guarantee that any episode is ever driven to completion.

The Info Dict
^^^^^^^^^^^^^

While the *info* `dict` is free to return any additional information
imaginable, there are a few keys that have an established meaning:

.. infodictkey:: "success"
    :type: bool

    is a bool indicating whether the episode has ended by reaching a "good"
    terminal state. Rendering wrappers may use this key to highlight the
    episode in a particular manner.

    If the step hasn't actually ended the episode, this key has no meaning. If
    the episode has ended and the key is absent, this must be interpreted as an
    indeterminate terminal state, and not necessarily as a bad one.

.. infodictkey:: "final_observation"
    :type: ~cernml.coi.ObsType
.. infodictkey:: "final_info"
    :type: ~cernml.coi.InfoDict

    are defined by `~gymnasium.wrappers.AutoResetWrapper`. They are added
    whenever an episode ends and :func:`~gymnasium.Env.reset()` is called
    automatically. They contain the observation and info from the last step of
    the previous episode, since in the return value of
    :func:`~gymnasium.Env.step()`, these values have been supplanted with those
    from :func:`~gymnasium.Env.reset()`.

.. infodictkey:: "episode"
    :type: dict[str, typing.Any]

    is defined by `~gymnasium.wrappers.RecordEpisodeStatistics`. It is a `dict`
    with the cumulative reward, the episode length in steps, and the length in
    time.

.. infodictkey:: "reward"
    :type: float

    is defined by `SeparableEnv` and `SeparableGoalEnv`. It contains the reward
    of the current step and is set by their default implementations of
    `~SeparableEnv.step()`.

Closing
^^^^^^^

The `~Problem.close()` method is called at the end of the lifetime of an
environment. This may happen after one full optimization run or after several.
No further calls to :func:`~gymnasium.Env.reset()` or
:func:`~gymnasium.Env.step()` will be made afterwards. This method should
release any resources that the environment has acquired in its
:meth:`~object.__init__()` method.

Env Rendering
^^^^^^^^^^^^^

The same rules for :ref:`guide/control_flow:Rendering` apply as for the other
classes. Automatic calls to `~Problem.render()` are usually handled by wrappers
like `~gymnasium.wrappers.HumanRendering` or
`~gymnasium.wrappers.RenderCollection`, and not by the environment itself.


Env Example
^^^^^^^^^^^

A typical execution loop for environments might look like this:

.. literalinclude:: minimal_env_loop.py
    :lines: 13-
    :linenos:
