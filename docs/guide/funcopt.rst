.. SPDX-FileCopyrightText: 2020 - 2025 CERN
.. SPDX-FileCopyrightText: 2023 - 2025 GSI Helmholtzzentrum für Schwerionenforschung
.. SPDX-FileNotice: All rights not expressly granted are reserved.
..
.. SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

Optimizing Points on an LSA Function
====================================

.. currentmodule:: cernml.coi

.. digraph:: inheritance_diagram
    :caption: "Fig. 4: Inheritance diagram of FunctionOptimizable"

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
            <tr>
                <td><i>optimization_space</i><br
                /><i>constraints</i></td>
            </tr>
        </table>
    >];

    fopt[label=<
        <table border="0" cellborder="1" cellspacing="0" cellpadding="4">
            <tr><td>cernml.coi.<b>FunctionOptimizable</b></td></tr>
            <tr>
                <td>get_initial_params(<i>t</i>: float, <i>seed</i
                >=None, <i>options</i>=None) → Params<br
                />compute_function_objective(<i>p</i>: Params, <i>t</i
                >: float) → float<br
                />get_optimization_space(<i>t</i>: float) → Space</td>
            </tr>
        </table>
    >];

    sopt -> problem;
    fopt -> problem;

Motivation
----------

The :doc:`core interfaces <core>` support classical numerical optimization and
reinforcement learning. In both cases, the cost function that is being
optimized is generally a mapping *f*: ℝⁿ → ℝ.

In accelerator controls, there are several situations in which either the
optimization space or the cost is not just a scalar or vector, but a function
of such over time, and one needs to optimize this function as a whole.

An example is the problem of beam steering in a synchrotron pre-accelerator.
The parameter to be optimized is the electric current delivered to the magnets.
This voltage varies during the duration of a cycle: It starts out at a *flat
bottom*, then it *ramps up* as the beam is being accelerated, reaches a *flat
top* during which the beam is extracted to a subsequent facility, and finally
*ramps down* to the flat bottom until the next cycle starts.

Over the course of such a cycle, the beam position has to be within strict
limits the entire time. This gives rise to an optimization problem: Adjust the
magnet current *at all times* such that the beam deviates as little as possible
from its ideal trajectory *at all times*.

Solution
--------

The `FunctionOptimizable` solves the problem of optimization over time by
reducing it to multiple subsequent optimizations. It does so by introducting
the concept of *skeleton points*. A skeleton point need not just be a single
point in time, it may also be a time *interval*. This makes sense e.g. in the
flat bottom or flat top of a current curve, where the function is constant.

Given these skeleton points, temporal optimization reduces to regular
optimization at each skeleton point. If the cost is a function over time as
well, the optimization problem must reduce it in some way – for example by
calculating the expectation or variance.

Incorporation Rules
-------------------

At CERN, functions over times typically have *incorporation rules* attached to
them, which describe how these functions may be modified by computer systems.
These rules are defined in a database individually for each function and for a
number of skeleton points on that function. They ensure e.g. that the flat top
actually stays flat, or that the slope of the ramp does not exceed a given
value.

One consequence is that it is not safe to optimize a function at a skeleton
point for which no incorporation rule is defined.

The :mod:`utils:cernml.lsa_utils` package provides utilities to the authors of
optimization problems that allow them to easily incorporate a desired change
into a function by applying these rules. Due to the above architecture,
incorporation requires communication with the rules database. The
:mod:`~utils:cernml.lsa_utils` package uses `PJLSA`_ for this communication. As
such, these utilities only work within the CERN network.

.. _PJLSA: https://gitlab.cern.ch/scripting-tools/pjlsa

Custom Skeleton Points
----------------------

The default and expected behavior of a `FunctionOptimizable` is that it lets
the user choose the skeleton points at which to optimize the functions, and to
be agnostic over the specific points at which it runs. Some authors might wish
to customize this choice, however.

Function optimization problems may override the method
`~FunctionOptimizable.override_skeleton_points()` and return a list of skeleton
points from it. In such a case, a host application should only optimize the
problem at these points and none other. It's still advisable to let a user
*review* these skeleton points before starting optimization. An optimization
problem should still handle the case that only a *subset* of the given skeleton
points are optimized.

An optimization problem that overrides this function should also be
`Configurable` and let the user configure the skeleton points in some
*customized* manner. For example, it could define a fixed interval, but let the
user choose a number of points *N*. The function
`~FunctionOptimizable.override_skeleton_points()` could then split the interval
into *N−1* equal sub-intervals and return their edges as skeleton points. This
could look like this:

.. code-block:: python

    >>> import typing as t
    >>> import numpy as np
    >>> from cernml.coi import (
    ...     FunctionOptimizable,
    ...     Configurable,
    ...     Config,
    ...     ConfigValues,
    ...     BadConfig,
    ... )
    >>> class Example(FunctionOptimizable, Configurable):
    ...     def __init__(self) -> None:
    ...         self._npoints = 5
    ...
    ...     def get_config(self) -> Config:
    ...         return Config().add(
    ...             'npoints', self._npoints, range(1, 10)
    ...         )
    ...
    ...     def apply_config(self, values: ConfigValues) -> None:
    ...         self._npoints = values.npoints
    ...
    ...     # Note the narrower return type, because we can.
    ...     def override_skeleton_points(self) -> t.List[float]:
    ...         return np.linspace(
    ...             1400.0, 1800.0, self._npoints
    ...         ).tolist()
    ...
    ...     # Rest of the implementation
    ...     ...
