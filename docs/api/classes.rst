..
    SPDX-FileCopyrightText: 2020-2024 CERN
    SPDX-FileCopyrightText: 2023-2024 GSI Helmholtzzentrum für Schwerionenforschung
    SPDX-FileNotice: All rights not expressly granted are reserved.

    SPDX-License-Identifier: MIT AND (GPL-3.0-or-later OR EUPL-1.2+)

:tocdepth: 3

Core Classes of This Package
============================

.. seealso::

    :doc:`/guide/core`
        User guide page on most classes introduced here.
    :doc:`/guide/control_flow`
        User guide page on the order in which the methods introduced here are
        expected to be called.
    :doc:`/guide/custom_optimizers`
        User guide page on specifically `~cernml.coi.CustomOptimizerProvider`.
    :doc:`/guide/funcopt`
        User guide page on specifically `~cernml.coi.FunctionOptimizable`.

.. automodule:: cernml.coi._classes
    :no-members:

.. currentmodule:: cernml.coi

.. autoclass:: Problem
    :inherited-members:

.. autoclass:: SingleOptimizable

.. autoclass:: FunctionOptimizable

.. class:: Env
    :module: cernml.coi

    Bases: `Problem`, `Generic`\ [`ObsType`, `ActType`]

    See `gymnasium.Env`. This is re-exported for the user's convenience.

.. autoclass:: HasNpRandom

Interfaces for Custom Per-Problem Algorithms
--------------------------------------------

.. seealso::

    :doc:`/guide/custom_optimizers`
        User guide page on this topic.

.. module:: cernml.coi._custom_optimizer_provider
.. currentmodule:: cernml.coi
.. autoclass:: CustomOptimizerProvider

.. entrypoint:: cernml.custom_optimizers

    :doc:`Entry points <pkg:specifications/entry-points>` defined under this
    this group are an alternative to direct implementation on the optimization
    problem itself. They should either point at a subclass of
    `CustomOptimizerProvider` or at a function that acts like
    `~CustomOptimizerProvider.get_optimizers()`. The syntax is
    :samp:`{module_name}:{ClassName}` and :samp:`{module_name}:{function_name}`
    respectively.

    A host application may load and invoke such an entry point *if and only if*
    the user selects an optimization problem whose name (including the
    namespace) matches the entry point name.

.. module:: cernml.coi._custom_policy_provider
.. currentmodule:: cernml.coi
.. autoclass:: CustomPolicyProvider

.. entrypoint:: cernml.custom_policies

    :doc:`Entry points <pkg:specifications/entry-points>` defined under this
    this group are an alternative to direct implementation on the environment
    itself. They should point at a subclass of
    `CustomPolicyProvider` with the syntaxa :samp:`{module_name}:{ClassName}`.
    The class must be instantiable by calling it with no arguments.

    A host application may load and invoke such an entry point *if and only if*
    the user selects an environment whose name (including the namespace)
    matches the entry point name.

.. autoclass:: Policy

Standard Metadata Keys
----------------------

.. seealso::

    :ref:`guide/core:Metadata`
        User guide section on this topic.

`Problem.metadata` is a mapping that describe the capabilities and
behavior of the given optimization problem. While any sort of data can be
stored in it, the following keys have a standardized meaning:

.. metadatakey:: "render_modes"
    :type: Sequence[str]
    :value: []

    The render modes that the optimization problem understands. Standard render
    modes are documented under `Problem.render()`. This replaces the deprecated
    key ``"render.modes"`` with the same meaning.

.. metadatakey:: "render_fps"
    :type: int | None
    :value: None

    Problems that support the render modes ``"rgb_array"`` or
    ``"rgb_array_list"`` are expected to set this value to the animation speed
    of the returned frames. The value is interpreted as frames per second.

.. metadatakey:: "cern.machine"
    :type: Machine
    :value: Machine.NO_MACHINE

    The accelerator that an optimization problem is associated with. Host
    applications can use this field to filter the set of problems presented to
    the user. Problems that are not associated with any specific CERN
    accelerator are free to omit this key. Laboratories outside of CERN are
    encouraged to define an analogous key that fits their use case.

.. metadatakey:: "cern.japc"
    :type: bool
    :value: False

    A boolean flag indicating that the problem's constructor expects an
    argument named *japc* of type :class:`~pyjapc.PyJapc`. Enable it if your
    class performs any machine communication via JAPC. Do not create your own
    :class:`~pyjapc.PyJapc` instance. Among other things, this ensures that the
    correct timing selector is set.

.. metadatakey:: "cern.cancellable"
    :type: bool
    :value: False

    A boolean flag indicating that the problem's constructor expects an
    argument named *cancellation_token* of type `cancellation.Token`. Enable it
    if your class ever enters any long-running loops that the user may want to
    interrupt. A classic example is the acquisition and validation of
    cycle-bound data.

.. note::

    Laboratories are encouraged to define their own metadata keys as necessary.

    Care should be taken that the values stored in the dictionary have a simple
    type (e.g. numbers, strings, and lists thereof) that is immutable and
    trivial to serialize and deserialize. Laboratories are encouraged to name
    their metadata keys in a namespaced manner, analogous to
    :mdkey:`"cern.machine"`.

Standard Render Modes
---------------------

.. seealso::

    :ref:`guide/core:Rendering`
        User guide section on this topic.

Render modes declare the ways in which an optimization problem may be
visualized. Problems list their supported modes in their :mdkey`"render_modes"`
metadata. Problems with no supported render mode cannot be visualized.

Users can pass a supported *render_mode* of their choosing either to `make()`
or to the `Problem` constructor directly. The problem is expected to store this
value in a `~Problem.render_mode` attribute. Calling `~Problem.render()` then
should react according to the initially chosen render mode.

.. rendermode:: None

    If no render mode is specified, no rendering should take place. Calling
    `~Problem.render()` should do nothing.

.. rendermode:: "human"
    :rtype: None

    The problem renders itself to the current display or the terminal in a way
    that is fit for human consumption. The display should update automatically,
    i.e. without the user explicitly calling `~Problem.render()`. Other methods
    may still call it internally to update the display whenever the problem's
    state changes.

.. rendermode:: "ansi"
    :rtype: str | io.StringIO

    The problem renders its current state in a terminal-style representation.
    The representation may contain newlines and `ANSI escape codes`_.

.. _ANSI escape codes: https://en.wikipedia.org/wiki/ANSI_escape_code

.. rendermode:: "rgb_array"
    :rtype: ~numpy.typing.NDArray[~numpy.uint]

    The problem renders its current state in a color image. The color image
    should be returned as a 3D array of shape :samp:`({width}, {height}, 3)`,
    where the last dimension denotes the colors *red*, *blue* and *green*.
    Values are in the range from 0 to 255 inclusive.

.. rendermode:: "matplotlib_figures"
    :rtype: ~matplotlib.figure.Figure \
        | Iterable[~matplotlib.figure.Figure \
        | tuple[str, ~matplotlib.figure.Figure]] \
        | Mapping[str, ~matplotlib.figure.Figure]

    The problem renders itself via :doc:`Matplotlib <mpl:index>` to one or more
    :class:`~matplotlib.figure.Figure` objects. The return value should include
    all figures whose contents have changed. Figures whose contents haven't
    changed needn't be returned again.

    The following return types are allowed:

    - a single :class:`~matplotlib.figure.Figure`;
    - an iterable of :class:`~matplotlib.figure.Figure`\ s or 2-tuples of
      `str` and :class:`~matplotlib.figure.Figure` or both;
    - a mapping with `str` keys and :class:`~matplotlib.figure.Figure` values.

    Strings are interpreted as window titles for their associated figure.

List-Like Render Modes
^^^^^^^^^^^^^^^^^^^^^^

There are also so-called *list-like render modes*. In these modes, the problem
should render itself automatically after each time step and store the resulting
*frame* in an internal buffer. Whenever `~Problem.render()` is called, no
rendering should be done and instead, all *frames* should be returned:

.. rendermode:: "ansi_list"
    :rtype: list[str] | list[io.StringIO]

    Like :rmode:`"ansi"`, but terminal-style representations are collected at
    each time step. Calling `~Problem.render()` returns the buffered frames.

.. rendermode:: "rgb_array_list"
    :rtype: list[~numpy.typing.NDArray[~numpy.uint]]

    Like :rmode:`"rgb_array"`, but color images are collected at each time
    step. Calling `~Problem.render()` returns the buffered frames.

.. note::
    You typically don't implement list-like modes yourself. Instead, if the
    user requests one of them via `make()`, your problem is wrapped in
    a `~gymnasium.wrappers.RenderCollection` wrapper and the non-list
    equivalent is passed to your :meth:`~object.__init__()` method.

Whether and when the frame buffer should be cleared is implementation-defined;
`~gymnasium.wrappers.RenderCollection` lets the user choose during
initialization. Typical choices are to clear it automatically after each
`~Problem.render()` call, or whenever :func:`~gymnasium.Env.reset()` or
`~SingleOptimizable.get_initial_params()` are called.

Supporting Types
----------------

The following types are not interfaces themselves, but are used by the core
interfaces of this package.

.. module:: cernml.coi._machine
.. currentmodule:: cernml.coi
.. autoclass:: Machine
    :undoc-members:

.. class:: Space
    :module: cernml.coi

    Bases: `Generic`\ [`T_co <TypeVar>`]

    See `gym:gymnasium.spaces.Space`. This is re-exported for the user's
    convenience.

.. autodata:: Constraint

.. data:: ParamType
    :type: typing.TypeVar

    The generic type variable for `SingleOptimizable`.
    This is exported for the user's convenience.

.. data:: ActType
    :type: typing.TypeVar

    The generic type variable for the actions of `~gymnasium.Env` and its
    subclasses. Reexported from Gymnasium for the user's convenience.

.. data:: ObsType
    :type: typing.TypeVar

    The generic type variable for the observables of `~gymnasium.Env` and its
    subclasses. Reexported from Gymnasium for the user's convenience.
