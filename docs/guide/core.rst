.. SPDX-FileCopyrightText: 2020 - 2025 CERN
.. SPDX-FileCopyrightText: 2023 - 2025 GSI Helmholtzzentrum für Schwerionenforschung
.. SPDX-FileNotice: All rights not expressly granted are reserved.
..
.. SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

The Core API
============

.. currentmodule:: cernml.coi

This page describes the various pieces of the common optimization interfaces.
You are invited to skip to a section that interests you, or to read the page
top to bottom, at your leisure.

Keep in mind that while these interfaces are the most important ones, there are
also others that provide important features. See, for example,
:doc:`configurable` and :doc:`custom_optimizers`.

The Interface Hierarchy
-----------------------

.. digraph:: inheritance_diagram
    :caption: "Fig. 1: Inheritance diagram of the core interfaces"

    rankdir = "BT";
    bgcolor = "#00000000";
    node [shape=plaintext, fontname="Open Sans", style=filled, fillcolor="white"];
    edge [style=dashed];

    problem[label=<
        <table border="0" cellborder="1" cellspacing="0" cellpadding="4">
            <tr><td>cernml.coi.<b>Problem</b></td></tr>
            <tr>
                <td>render() → Any<br
                />close() → None</td>
            </tr>
            <tr>
                <td><i>metadata</i>: dict<br
                /><i>render_mode</i>: str | None = None<br
                /><i>unwrapped</i>: Problem</td>
            </tr>
        </table>
    >];

    sopt[label=<
        <table border="0" cellborder="1" cellspacing="0" cellpadding="4">
            <tr><td>cernml.coi.<b>SingleOptimizable</b></td></tr>
            <tr>
                <td>get_initial_params(<i>seed</i>=None, <i>options</i>=None) → Params<br
                />compute_single_objective(<i>p</i>: Params) → float</td>
            </tr>
            <tr><td><i>optimization_space</i></td></tr>
        </table>
    >];

    env[label=<
        <table border="0" cellborder="1" cellspacing="0" cellpadding="4">
            <tr><td>gymnasium.<b>Env</b></td></tr>
            <tr>
                <td>reset(<i>seed</i>=None, <i>options</i>=None) → tuple[Obs, dict]<br
                />step(<i>action</i>: Action) → tuple[Obs, float, bool, bool, dict]</td>
            </tr>
            <tr>
                <td><i>action_space</i><br
                /><i>observation_space</i></td>
            </tr>
        </table>
    >];

    optenv[label=<
        <table border="0" cellborder="1" cellspacing="0" cellpadding="4">
            <tr><td>cernml.coi.<b>OptEnv</b></td></tr>
        </table>
    >];

    optenv -> sopt -> problem;
    optenv -> env -> problem;

The interfaces are designed in a modular fashion: depending on the algorithms
that an optimization problem supports, it either implements `SingleOptimizable`
(for classical single-objective optimization), `Env` (for reinforcement
learning) or both. The `Problem` interface captures the greatest common
denominator – that, which all interfaces have in common.

As a convenience, this package also provides the `OptEnv` interface. It is
simply an intersection of `SingleOptimizable` and `Env`. This means that
implementing it is the same as implementing both of its bases. At the same
time, every class that implements both base interfaces also implements
`OptEnv`. A demonstration:

    >>> import gymnasium
    >>> from cernml import coi
    ...
    >>> class Indirect(coi.SingleOptimizable, gymnasium.Env):
    ...     optimization_space = ...
    ...     observation_space = ...
    ...     action_space = ...
    ...
    >>> issubclass(Indirect, coi.OptEnv)
    True

Minimal Implementations
-----------------------

This section shows you the *absolute* bare minimum to write any optimization
problem at all. They're intended to get your feet off the ground if you are new
to this library. They are not interesting optimization problems. Anything
non-trivial (e.g. communicating with an external machine) will require some
additional steps. See :doc:`/tutorials/implement-singleoptimizable` for a more
comprehensive tutorial.

Single-Objective Optimization Problems
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For a minimal working example, you should inherit from
`cernml.coi.SingleOptimizable` to have it fill in as many defaults as possible.
With it as a superclass, you only have to fill in three missing pieces:

1. `~SingleOptimizable.get_initial_params()` to give the *initial point* of an
   optimization;
2. `~SingleOptimizable.compute_single_objective()` as the *objective function*
   to be minimized [#min]_;
3. `~SingleOptimizable.optimization_space` to specify the problem's *domain*,
   i.e. valid inputs to the objective function. See also
   :ref:`guide/core:spaces` for more information.

.. [#min] The objective function is also called *cost function* or *loss
   function*. If you have a maximization problem, you can always convert it to
   a minimization problem by flipping the sign of the figure of interest.

You also have to *register* your class so that the central function
`cernml.coi.make()` can instantiate it. The page on :doc:`registration` has
more information.

This is a minimal, runnable example problem:

.. literalinclude:: minimal_sopt_class.py
    :lines: 9-
    :linenos:

Single-Objective Function Optimization Problems
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. seealso::
    :doc:`funcopt`
        User guide page on function optimization problems.

For a minimal working example, you should inherit from
`cernml.coi.FunctionOptimizable` to have it fill in as many defaults as
possible. With it as a superclass, you only have to fill in three missing
pieces:

1. `~FunctionOptimizable.get_initial_params()` to give the *initial point* for
   each individual optimization;
2. `~FunctionOptimizable.compute_function_objective()` as the *objective function*
   to be minimized [#min]_;
3. `~FunctionOptimizable.get_optimization_space()` to specify the *domain*,
   i.e. valid inputs to the objective function. See also
   :ref:`guide/core:spaces` for more information.

You also have to *register* your class so that the central function
`cernml.coi.make()` can instantiate it. The page on :doc:`registration` has
more information.

This is a minimal, runnable example problem:

.. literalinclude:: minimal_fopt_class.py
    :lines: 9-
    :linenos:

Reinforcement Learning Environments
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For a minimal working example, you inherit from `gymnasium.Env` and fill in the
X missing pieces:

1. :func:`~gymnasium.Env.reset()` to initialize the environment for a new
   episode and receive an initial observation;
2. :func:`~gymnasium.Env.step()` to take an action in the current episode;
3. `~gymnasium.Env.observation_space` to specify the domain of *observations*
   that are returned by :func:`~gymnasium.Env.reset()` and
   :func:`~gymnasium.Env.step()`;
4. `~gymnasium.Env.action_space` to specify the domain of *actions* that are
   accepted by :func:`~gymnasium.Env.step()`. See also :ref:`guide/core:spaces`
   for more information.

You also have to *register* your class so that the central function
`cernml.coi.make()` can instantiate it. The page on :doc:`registration` has
more information.

This is a minimal, runnable example problem:

.. literalinclude:: minimal_env_class.py
    :lines: 9-
    :linenos:

Running Your Optimization Problem
---------------------------------

.. seealso::
    :doc:`control_flow`
        User guide page with detailed information on each kind of execution
        loop.

Optimization problems – no matter whether based on `Env`, `SingleOptimizable`
or another interface – are expected to be run as *plugins* into a *host*
application. While the Geoff project maintains a `reference implementation
<https://gitlab.cern.ch/geoff/geoff-app/>`_ of such a host application,
institutes and users are encouraged to write their own host applications,
tailored to their specific needs and re-using `components of the broader Geoff
project <https://gitlab.cern.ch/geoff/>`_ as necessary.

Typically, host applications end up implementing one kind or another of
*execution loop* executes an algorithm (e.g. a numerical optimizer or an RL
policy) on a given problem. Minimal execution loops for the different kinds of
problems (which might be useful for debugging) may look like this:

.. tab:: SingleOptimizable

    .. literalinclude:: minimal_sopt_loop.py
        :lines: 13-
        :linenos:

.. tab:: FunctionOptimizable

    .. literalinclude:: minimal_fopt_loop.py
        :lines: 17-
        :linenos:

.. tab:: Env (Evaluation)

    .. literalinclude:: minimal_env_loop.py
        :lines: 13-
        :linenos:

While these examples are very bare-bones, various libraries already provide
pre-packaged execution loops with a number of additional conveniences:

:doc:`Stable Baselines 3 <sb3:index>`
    supports the `Env` API and RL environments can be passed directly to the
    various :samp:`{agent}.learn()` methods; in addition, the package provides
    a function :func:`~stable_baselines3.common.evaluation.evaluate_policy()`
    to solve a problem with a given agent or policy.
`cernml-rltools <https://gitlab.cern.ch/geoff/cernml-rltools/>`_
    provides a module ``cernml.rltools.envloop`` with an older and more
    general-purpose implementation of the environment interaction loop.
:doc:`cernml-coi-optimizers <optimizers:index>`
    provides a uniform interface for solvers of `SingleOptimizable` problems.
    Its general-purpose :func:`~cernml.optimizers.solve()` function is directly
    compatible with the COI.

In addition, many optimizers like :func:`scipy.optimize.minimize()` and
`Py-BOBYQA <https://numericalalgorithmsgroup.github.io/pybobyqa/>`_ are able to
consume `SingleOptimizable` with only minor adjustments.

Spaces
------

Optimization is always executed over a certain numeric *domain*, i.e. a space
of allowed values. These domains are encapsulated by Gym's concept of
a `Space`. While Gym provides many different kinds of spaces (discrete,
continuous, aggregate, …), the COI only support `~gymnasium.spaces.Box` at this
time. This restriction may be lifted in the future, depending on user feedback.

The interfaces make use of spaces as follows:

`SingleOptimizable.optimization_space`
    the domain of valid inputs to
    `~SingleOptimizable.compute_single_objective()`;

`Env.action_space <gymnasium.Env.action_space>`
    the domain of valid inputs to :func:`~gymnasium.Env.step()`;

`Env.observation_space <gymnasium.Env.observation_space>`
    the domain of valid observations returned by :func:`~gymnasium.Env.reset()`
    and :func:`~gymnasium.Env.step()`.

Naming Your Quantities
----------------------

In many cases, your objective function and parameters directly correspond to
machine parameters. For example, many optimization problems might only scale
their parameters and otherwise send them unmodified to the machine via JAPC.
Similarly, the objective function might only be a rescaled or inverted reading
from a detector on the accelerator.

In such cases, it is useful to declare the meaning of your quantities. A host
application may use this to annotate its graphs of the parameters and objective
function. The `SingleOptimizable` class provides three attributes for this
purpose:

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
are free to define them inside your :meth:`~object.__init__()` method or change
them at run-time. This is useful because some optimization problems might
decide to be configurable in the exact devices they talk to.

You are free not to define these attributes at all. In this case, the host
application will see the inherited default values and assume no particular
meaning of your quantities.

Metadata
--------

Every optimization problem should have a class attribute called
`Problem.metadata`, which is a dict with string keys. The dict should be
defined at the class level and immutable [#mdimmut]_. It communicates
fundamental properties of the class and how a host application can use it.

While the API reference contains the full definition of the
:ref:`api/classes:standard metadata keys`, the following is an abridged
version:

:mdkey:`"render_modes"`
    the render modes that the optimization problem understands (see
    :ref:`guide/core:Rendering`);

:mdkey:`"cern.machine"`
    the accelerator that an optimization problem is associated with (see
    `cernml.coi.Machine`);

:mdkey:`"cern.japc"`
    a boolean flag indicating whether the problem's constructor expects an
    argument named *japc* of type :class:`~japc:pyjapc.PyJapc`;

:mdkey:`"cern.cancellable"`
    A boolean flag indicating whether the problem's constructor expects
    a cancellation token. (see :ref:`guide/cancellation:Cancellation`).

.. [#mdimmut] While authors of optimization problems are strongly encouraged to
   make `~Problem.metadata` immutable and class-scoped, host applications
   cannot rely on this. Edge cases are known where the attribute is either
   instance-scoped or the dict is swapped out for another. No cases are known
   where an existing dict is modified in-place.

Rendering
---------

The metadata entry :mdkey:`"render_modes"` allows a problem to declare that its
internal state can be visualized. It should be a list of strings where each
string is a supported render mode. Host applications may pick one of these
strings and pass it to the problems :meth:`~Problem.render()` method. For this
to work, render modes need to have well-defined semantics.

The following render modes are standardized by either Gym or this package:

:rmode:`"human"`
    The default mode, for interactive use. This should e.g. open a window and
    display the problem's current state in it. Displaying the window should not
    block control flow.

:rmode:`"ansi"`
    Return a text-only representation of the problem. This may contain e.g.
    terminal control codes for color effects.

:rmode:`"rgb_array"`
    Return a Numpy array representing color image data.

:rmode:`"matplotlib_figures"`
    Return a list of Matplotlib :class:`~matplotlib.figure.Figure` objects,
    suitable for embedding into a GUI application.

See the `~cernml.coi.Problem.render()` docs for a full spec of each render
mode.

Closing
-------

Some optimization problems have to acquire certain resources in order to
perform their tasks. Examples include:

- spawning processes,
- starting threads,
- subscribing to JAPC parameters.

While Python garbage-collects objects which are no longer accessible (including
`Problem` instances), some of these resources require manual function calls in
order to be properly cleaned up.

If such is the case for an optimization problem, it should override the
`~Problem.close()` method and define all such actions in it. A host application
is required to call `~Problem.close()` when it has no more need for an
optimization problem.

All classes that inherit from `Problem` automatically are :term:`context
managers <context manager>` that can be used in :keyword:`with` blocks.
Whenever the :keyword:`with` block is exited, `~Problem.close()` gets called
automatically.

.. note::

    If, for some reason, you are dealing with an optimization problem that
    doesn't explicitly subclass `Problem`, you can use the `contextlib.closing`
    adapter:

    .. code-block:: python

        from contextlib import closing

        with closing(MyProblem(...)) as problem:
            optimize(problem)

    This ensures that `~Problem.close()` is called under all circumstances –
    even if an exception occurs.

Additional Restrictions
-----------------------

For maximum compatibility, this API puts the following *additional*
restrictions on environments:

- The `~gymnasium.Env.observation_space`, `~gymnasium.Env.action_space` and
  `~SingleOptimizable.optimization_space` must all be `Boxes
  <gymnasium.spaces.Box>`. The only exception is if the environment is
  a `GoalEnv`: in that case, `~gymnasium.Env.observation_space` must be
  `~gymnasium.spaces.Dict` (with exactly the three expected keys) and the three
  required sub-spaces must be `Boxes <gymnasium.spaces.Box>`.
- If the environment supports any rendering at all, it should support at least
  the *human*, *ansi* and *matplotlib_figures*. The former two facilitate
  debugging and stand-alone usage, the latter makes it possible to embed the
  environment into a GUI.
- At CERN, The environment metadata must contain a key :mdkey:`"cern.machine"`
  with a value of type `Machine`. It tells users which CERN accelerator the
  environment belongs to. Outside of CERN, authors are free to omit this key
  and institutes are allowed to define a category key of their own.

For the convenience of problem authors, this package provides a function
`check()` that verifies these requirements on a best-effort basis. If you
package your problem, we recommend adding a unit test to your package that
calls this function and exercise it on every CI job. CERN users are encouraged
to consult the `Acc-Py guidelines on testing
<https://wikis.cern.ch/display/ACCPY/Testing>`_ for further information.
