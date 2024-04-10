..
    SPDX-FileCopyrightText: 2020-2024 CERN
    SPDX-FileCopyrightText: 2023-2024 GSI Helmholtzzentrum für Schwerionenforschung
    SPDX-FileNotice: All rights not expressly granted are reserved.

    SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

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


.. code-block:: python

    import gymnasium as gym
    from cernml import coi

    class Indirect(coi.SingleOptimizable, gym.Env):
        ...

    assert issubclass(Indirect, coi.OptEnv)


Metadata
--------

Every optimization problem should have a class attribute called
`Problem.metadata`, which is a dict with string keys. The dict must be defined
at the class level and immutable. It communicates fundamental properties of the
class and how a host application can use it.

The following keys are defined and understood by this package:

``"render_modes"``
    the render modes that the optimization problem understands (see
    :ref:`guide/core:Rendering`);

``"cern.machine"``
    the accelerator that an optimization problem is associated with;

``"cern.japc"``
    a boolean flag indicating whether the problem's constructor expects an
    argument named *japc* of type :class:`~japc:pyjapc.PyJapc`;

``"cern.cancellable"``
    A boolean flag indicating whether the problem's constructor expects an
    argument named *cancellation_token* of type `cancellation.Token
    <cernml.coi.cancellation.Token>` (see
    :ref:`guide/cancellation:Cancellation`).

See the :attr:`API docs<Problem.metadata>` for a full spec.

Rendering
---------

The metadata entry ``"render_modes"`` allows a problem to declare that its
internal state can be visualized. It should be a list of strings where each
string is a supported render mode. Host applications may pick one of these
strings and pass it to the problems {meth}`~Problem.render()` method. For this
to work, render modes need to have well-defined semantics.

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

.. warning::

    The `~Problem.close()` method is *not* called after an optimization
    procedure is done. In particular, a host application may perform several
    optimization runs on the same problem and call `~Problem.close()` only at
    the very end. Furthermore, an arbitrary amount of time may pass between the
    last call to `~SingleOptimizable.compute_single_objective()` and the call
    to `~Problem.close()`.

.. note::

    If you want to use an optimization problem in your own application or
    script, consider using the :func:`~contextlib.closing()` context manager:

    .. code-block:: python

        from contextlib import closing

        with closing(MyProblem(...)) as problem:
            optimize(problem)

    The context manager ensures that `~Problem.close()` is called under all
    circumstances – even if an exception occurs.

Spaces
------

Optimization is always executed over a certain numeric *domain*, i.e. a space
of allowed values. These domains are encapsulated by Gym's concept of
a `Space`. While Gym provides many different kinds of spaces (discrete,
continuous, aggregate, …), this package for now only supports
`~gymnasium.spaces.Box` for maximum portability. This restriction may be lifted
in the future.

In addition, box spaces are for now restricted to the bounds [−1; +1]. This
restriction, too, may be lifted in the future.

The interfaces make use of spaces as follows:

`SingleOptimizable.optimization_space`
    the domain of valid inputs to
    `~SingleOptimizable.compute_single_objective()`;

`Env.action_space <gymnasium.Env.action_space>`
    the domain of valid inputs to :func:`~gymnasium.Env.step()`;

`Env.observation_space <gymnasium.Env.observation_space>`
    the domain of valid observations returned by :func:`~gymnasium.Env.reset()`
    and :func:`~gymnasium.Env.step()`.

Additional Restrictions
-----------------------

For maximum compatibility, this API puts the following *additional*
restrictions on environments:

- The `~gymnasium.Env.observation_space`, `~gymnasium.Env.action_space` and
  `~SingleOptimizable.optimization_space` must all be `Boxes
  <gymnasium.spaces.Box>`. The only exception is if the environment is
  a `GoalEnv`: in that case, `~gymnasium.Env.observation_space` must be
  `~gymnasium.spaces.Dict` (with exactly the three expected keys) and the
  ``"observation"`` sub-space must be a `~gymnasium.spaces.Box`.
- The `~gymnasium.Env.action_space` and the
  `~SingleOptimizable.optimization_space`  must have the same shape; They must
  only differ in their bounds. The bounds of the action space must be symmetric
  around zero and normalized (equal to or less than one).
- If the environment supports any rendering at all, it should support at least
  the *human*, *ansi* and *matplotlib_figures*. The former two facilitate
  debugging and stand-alone usage, the latter makes it possible to embed the
  environment into a GUI.
- The environment metadata must contain a key ``"cern.machine"`` with a value
  of type `Machine`. It tells users which CERN accelerator the environment
  belongs to.
- Rewards must always lie within the defined reward range and objectives within
  the defined objective range. Both ranges are unbounded by default.
- The problems must never diverge to NaN or infinity.

For the convenience of problem authors, this package provides a function
`check()` that verifies these requirements on a best-effort basis. If you
package your problem, we recommend adding a unit test to your package that
calls this function and exercise it on every CI job. See the `Acc-Py
guidelines`_ on testing for more information.

.. _Acc-Py guidelines: https://wikis.cern.ch/display/ACCPY/Testing
