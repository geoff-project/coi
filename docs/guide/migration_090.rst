..
    SPDX-FileCopyrightText: 2020-2024 CERN
    SPDX-FileCopyrightText: 2023-2024 GSI Helmholtzzentrum für Schwerionenforschung
    SPDX-FileNotice: All rights not expressly granted are reserved.

    SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

Migration Guide for COI v0.9
============================

.. currentmodule:: cernml.coi

.. seealso::

    :ref:`Changelog for Unreleased Version<changelog:Unreleased>`
        List of all changes, including backwards-compatible ones, released in
        this version.
    :doc:`gym:content/migration-guide`
        Corresponding migration guide of the Gymnasium package.

Version 0.9 of this package is the first to be based on Gymnasium_ rather than
its predecessor, Gym_. The new package changes several core aspects of its API,
which this package has to adapt to. At the same time, the opportunity has been
taken to introduce more breaking changes than in several previous major version
bumps.

This page collects all changes that are considered breaking and how to upgrade
your code to the new version.

.. _Gymnasium: https://github.com/Farama-Foundation/Gymnasium/
.. _Gym: https://github.com/openai/gym/

Minimum Python Version is now 3.9
---------------------------------

Both the COI and Gymnasium have **dropped support for Python 3.7**. Gymnasium
now requires at least Python 3.8, the COI require at least Python 3.9 [#]_.
While the two versions are largely backwards-compatible in the context where
the COI typically get used, Python 3.9 has added **a lot of deprecation
warnings**. We strongly recommend to run your code in `Development Mode`_
(added in Python 3.7).

Please refer to their respective release notes to see if
anything you require has been removed:

- `What’s New In Python 3.8 <Py3.8 Release Notes>`_
- `What’s New In Python 3.9 <Py3.9 Release Notes>`_

.. [#] The reason for the discrepancy is that Acc-Py never supported Python 3.8
   and has already added support for Python 3.11. We see little value in
   supporting Python 3.8, but please contact us if you require it.

.. _Development Mode: https://docs.python.org/3/library/devmode.html
.. _Py3.8 Release Notes: https://docs.python.org/3/whatsnew/3.8.html
.. _Py3.9 Release Notes: https://docs.python.org/3/whatsnew/3.9.html

New Gymnasium Step API
----------------------

Gymnasium overhauls the signatures of `Env.reset() <gymnasium.Env.reset>` and
`Env.step() <gymnasium.Env.step>`, expecting new arguments and return values.
This section only summarizes each change, please find the details in the
:doc:`gym:content/migration-guide`.

- `Env.reset() <gymnasium.Env.reset>` now returns 2 values instead of one:
  *info* has been added to the existing return value *obs*. This is another
  occurrence of :ref:`guide/control_flow:the info dict`.
- `Env.reset() <gymnasium.Env.reset>` now accepts two keyword-arguments, both
  optional: *seed* and *options*. While *options* may contain custom resetting
  options and doesn't do anything by default, *seed* should be passed through
  to the base implementation. This re-seeds `Env.np_random
  <gymnasium.Env.np_random>`.
- `Env.step() <gymnasium.Env.step>` now returns 5 values instead of 4: *done*
  has been replaced with *terminated* and *truncated*.
- The `~gymnasium.wrappers.TimeLimit` wrapper no longer adds the key
  ``"TimeLimit.truncated"`` to :ref:`guide/control_flow:the info dict`. This is
  no longer necessary, since the *truncated* flag returned by `Env.step()
  <gymnasium.Env.step>` now communicates this information.
- A new wrapper `~gymnasium.wrappers.StepAPICompatibility` may be added to an
  environment by passing *apply_api_compatibility* to `~.coi.make()`. It takes
  an environment that follows the old API and exposes the new API to the
  outside. It is `scheduled for removal <apply_api_compatibility_removal_>`_ in
  Gymnasium 1.0.

.. _apply_api_compatibility_removal:
    https://github.com/Farama-Foundation/Gymnasium/pull/535/commits/
    e49f9362fa1d4d5eacd39502c686e261fd0dc2fb

New API for Single-Objective Optimization
-----------------------------------------

The API of `SingleOptimizable` and `FunctionOptimizable` has been changed as
minimally as possible to stay in line with the Gymnasium API:

- The method `~SingleOptimizable.get_initial_params()` of *both* interfaces now
  accepts two keyword-arguments, both optional: *seed* and *options*. While
  *options* may contain custom resetting options and doesn't do anything by
  default, *seed* should be passed through to the base implementation. This
  re-seeds `Problem.np_random`.

.. note::

    Unlike :func:`~gymnasium.Env.reset()`,
    `~SingleOptimizable.get_initial_params()` does *not* return an *info* dict.
    While useful information could be returned, we consider such a return value
    too surprising for users. If you absolutely need to return additional
    information from `~SingleOptimizable.get_initial_params()`, consider
    passing a dict in *options* and filling it inside your implementation.

    Please feel free to contact the developers if you would prefer an *info*
    dict to be returned by these methods.

Changes to Environment Reseeding
--------------------------------

- The method ``Env.seed()`` has been removed in favor of the new *seed*
  parameter to the various resetting functions (see
  :ref:`guide/migration_090:New Gymnasium Step API` and
  :ref:`guide/migration_090:New API for Single-Objective Optimization`).
- `gymnasium.Env.np_random` is a random number generator for exclusive use by
  the environment. **It should be preferred over other sources of randomness.**
- For problems that don't subclass `~gymnasium.Env`, `Problem.np_random`
  provides the same functionality.
- If you do use other sources of randomness, e.g. `Space.sample()
  <gymnasium.spaces.space.Space.sample>`, you must make sure to re-seed them
  correctly whenever the *seed* parameter is passed to either of your resetting
  functions.

.. warning::

    Do not use the same seed to re-seed multiple independent random-number
    generators! Doing this will cause all RNGs to produce the same sequence of
    random numbers. Instead, re-seed one of them and derive new sub-seeds from
    it. For example:

    .. code-block:: python

        class MyEnv(Env):
            ...
            def reset(self, *, seed=None, options=None):
                # Reseed central RNG.
                super().reset(seed=seed)
                if seed is not None:
                    # Derive seeds for other RNGs from it.
                    next_seed = self.np_random.bit_generator.random_raw
                    self.observation_space.seed(next_seed())
                    self.action_space.seed(next_seed())
                ...
                return self.observation_space.sample(), {}

.. seealso::

    `Best Practices for Using NumPy's Random Number Generators`_
        An article written by Albert Thomas with recommendations for safe
        reseeding of Numpy RNGs as of January 26, 2024.

    :meth:`numpy.random.Generator.spawn()`
        Method of NumPy RNGs to create new child generators. Available with
        NumPy 1.25 or higher.

    :meth:`numpy.random.SeedSequence.spawn()`
        Method to create new seed sequences from an existing one. Available
        with NumPy 1.25 or higher.

.. _Best Practices for Using NumPy's Random Number Generators:
    https://blog.scientific-python.org/numpy/numpy-rng/

New Rendering API
-----------------

Gymnasium also overhauls the API used to render environments. Since the COI use
the exact same API, this also concerns the other interfaces in equal measure.
This section only summarizes each change, please find the details in the
:doc:`gym:content/migration-guide`.

- `Problem.render()` no longer accepts a *render_mode* argument. Instead, the
  render mode is expected to be set once per environment at time of
  instantiation.
- All problems are expected to accept a keyword argument *render_mode* and
  store it in a new attribute `Problem.render_mode`.
- The functions :func:`gymnasium.make()` and `cernml.coi.make()` now always
  accept an argument *render_mode*. They inspect the argument as well as
  the environment's allowed render modes and pass either the requested or
  a compatible render mode on to the environment's :meth:`~object.__init__()`
  method.
- The `~Problem.metadata` key ``"render.modes"`` has been renamed to
  :mdkey:`"render_modes"`. (The point has been replaced with underscore.) The
  meaning of the key has not changed. (See
  :ref:`guide/migration_090:Deprecations`)
- To ensure compliance with these changes, `Problem.__init__() <Problem>`
  now accepts a new *render_mode* argument. It automatically compares the
  passed value with :samp:`{self}.metadata["render_modes"]` and raises
  `ValueError` on unknown render modes. It also emits a `DeprecationWarning` if
  it encounters the metadata key ``"render.modes"``.

Render Mode Changes
-------------------

In addition to the above changes to how the render mode is passed around,
Gymnasium also made changes to how render modes behave. Most of these changers
concern automatic rendering whenever a **state-changing method** is called on
a problem. These methods are:

- for `~gymnasium.Env`: :func:`~gymnasium.Env.reset()` and
  :func:`~gymnasium.Env.step()`;
- for `SingleOptimizable`: `~SingleOptimizable.get_initial_params()` and
  `~SingleOptimizable.compute_single_objective()`;
- for `FunctionOptimizable`: `~FunctionOptimizable.get_initial_params()` and
  `~FunctionOptimizable.compute_function_objective()`.

The render modes have changed as follows:

- If the render mode is ``"human"``, all problems are now expected to call
  their own `~Problem.render()` method automatically whenever either of the
  *state-changing methods* are called. In all other render modes, users are
  still expected to call `~Problem.render()` manually between iterations.

- Gymnasium defines new render modes :rmode:`"rgb_array_list"` and
  :rmode:`"ansi_list"`. If the user requests one of these modes via `make()`,
  but the environment only supports its non-list counterpart, the environment
  is wrapped in a `~gymnasium.wrappers.RenderCollection` wrapper and the
  non-list mode is passed to the environment's :meth:`~object.__init__()`
  method.

  `~gymnasium.wrappers.RenderCollection` automatically calls
  `~Problem.render()` on every call to a *state-changing method* and stores the
  result (called a *frame*) in an internal buffer. Whenever the user calls
  `~Problem.render()`, no rendering is done; instead, all *frames* are removed
  from the internal buffer and returned.

- If the user requests the render mode :rmode:`"human"` via `make()`, but the
  environment only supports :rmode:`"rgb_array"` or :rmode:`"rgb_array_list"`,
  the environment is wrapped in a new `~gymnasium.wrappers.HumanRendering`
  wrapper and one of the supported modes is passed to the environment's
  :meth:`~object.__init__()` method. The results of `~Problem.render()` are
  then displayed to the user via the PyGame_ library.

To summarize how `make()` passes on the *render_mode* parameter:

==================== ========================= ====================
User requests        Environment supports      Environment receives
==================== ========================= ====================
``None``             ``[]``                    ``None``
``"rgb_array_list"`` ``["rgb_array"]``         ``"rgb_array"``
``"ansi_list"``      ``["ansi", "ansi_list"]`` ``"ansi_list"``
``"human"``          ``["rgb_array"]``         ``"rgb_array"``
``"human"``          ``["rgb_array_list"]``    ``"rgb_array_list"``
==================== ========================= ====================

.. _PyGame: https://www.pygame.org/wiki/about

New Registration API
--------------------

In previous versions, the COI simply re-used code from the Gym_ package to
instantiate its own registry of optimization problems, which was not supported,
but worked as intended for all purposes. Since then, Gymnasium_ has made
numerous changes to its registration code that preclude this approach from
working.

Consequently, registration has been reimplemented. in the new
`cernml.coi.registration` module. The implementation generally follows that of
Gymnasium. Please refer to the module documentation for a comprehensive list of
changes.

Generally, old code should work without modifications. However, the new code
places a greater emphasis on lazy loading of modules and the new code provides
:ref:`guide/registration:Lazy Registration via Entry Points`.

Revamp of the Abstract Base Classes
-----------------------------------

One of the core features of the COI is that they implement `structural
subtyping`_: Whether an object implements any of the interfaces is determined
at runtime by searching them for the required members. Previously, the check
was extremely primitive and only verified each member by name.

This code has since been completely reworked and based on the `Protocol` class,
added in Python 3.8. The checks are now stricter, meaning that classes that
used to pass as instances of e.g. `Problem` or `SingleOptimizable` no longer do
so.

When migrating your code, please consider the following:

- The attributes `~SingleOptimizable.optimization_space`,
  `~gymnasium.Env.observation_space` and `~gymnasium.Env.action_space` are no
  longer set to None in the base classes, but rather declared as as
  :term:`annotation`. As a consequence, your class must now define them itself
  in order to pass as one of the interfaces. If not, the class will pass *most*
  instance checks, but fail others.

  Two kinds of situation are known to be buggy:

  1. testing :samp:`issubclass({MyClass}, coi.SingleOptimizable)` when
     :samp:`{MyClass}` doesn't subclass `SingleOptimizable` and the expression
     :samp:`{MyClass}.optimization_space` would raise an `AttributeError`;
  2. testing :samp:`issubclass({MyClass}, coi.OptEnv)` and the expression
     :samp:`{MyClass}.optimization_space` would raise an `AttributeError` (no
     matter whether you subclass `SingleOptimizable` or not).

  Tests of the form :samp:`isinstance({obj}, coi.OptEnv)` should work as
  intended under all circumstances.

- A large family of :doc:`/api/typeguards` has been added. They make it easier
  to require that an instance or class implement a specific interface. They're
  based on `TypeGuard` and so compatible with static type checkers like MyPy_.

- There is now a split between the :doc:`abstract base classes </api/classes>`,
  which are supposed to be subclassed by **authors of optimization problems**
  and come with a few convenience features, and the :doc:`protocols
  </api/protocols>`, which are supposed to be used for type annotations and
  interface checks by **authors of host applications** and don't come with any
  implementation logic of their own.

.. _structural subtyping:
    https://typing.readthedocs.io/en/latest/source/protocols.html
.. _MyPy: https://mypy.readthedocs.io/

Miscellaneous Minor Breaking Changes
------------------------------------

The following changes all either break compatibility or anticipate breaking
changes as well. Unlike the previous changes, however, they concern less
commonly used features of the COI.

- The attribute ``objective_range`` **has been removed** from
  `SingleOptimizable` and `FunctionOptimizable`. This has been done in
  anticipation of the removal of the now deprecated
  `gymnasium.Env.reward_range`. See below under
  :ref:`guide/migration_090:Deprecations`.

- `~gymnasium_robotics.core.GoalEnv`, the interface for multi-goal RL
  environments, **has been moved** from Gymnasium to the new package
  :doc:`Gymnasium-Robotics <gymrob:README>`. Users who wish to use the API
  without installing the package may use `cernml.coi.GoalEnv`. If
  Gymnasium-Robotics is installed, this is a simple re-export of its
  definition. Otherwise, this is a reimplementation of the interface.

- Unlike its predecessor, Gymnasium is type-annotated. If you use a static type
  checker like MyPy_, it might now refuse code that previously type-checked
  because Gym types were treated like `Any`.

- The entry point for custom :doc:`/api/checkers` has been renamed from
  ``cernml.coi.checkers`` to :ep:`cernml.checkers`. This is for consistency
  with other entry points defined by this package.

Deprecations
------------

The following features are now considered deprecated and planned to be removed
in future versions of Gymnasium or the COI.

.. _Removal in Gymnasium 1.0:
    https://github.com/Farama-Foundation/Gymnasium/pull/535

- :doc:`gym:api/wrappers` looking up unknown attributes in the wrapped
  environment instead is deprecated and slated for `removal in Gymnasium 1.0`_.
  Any use of this behavior should be replaced with explicit calls to the new
  method `Problem.get_wrapper_attr()`.

- The `~Problem.metadata` key ``"render.modes"`` has been renamed. Please
  replace any occurrence with the name :mdkey:`"render_modes"` (underscore
  ``_`` instead of a period ``.``). The COI currently still accept the
  deprecated spelling but issue a warning. The old key is planned to be ignored
  starting with COI v0.10.0 or higher.

- The attribute `gymnasium.Env.reward_range` is slated for `removal in
  Gymnasium 1.0`_ with no replacement. The cited reason is a lack of use both
  by environments and RL algorithms.

- The argument *autoreset* to :func:`gymnasium.make()`,
  :func:`gymnasium.register()`, `cernml.coi.make()`, and
  `cernml.coi.register()` is slated for `removal in Gymnasium 1.0`_. To get the
  same functionally, use the *additional_wrappers* and pass
  a `~gymnasium.envs.registration.WrapperSpec` that points to the
  `~gymnasium.wrappers.AutoResetWrapper` class:

  .. code-block:: python

    register(
        "MyNamespace/MyEnv-v1",
        ...,
        additional_wrappers=(
            WrapperSpec(
                name="AutoResetWrapper",
                entry_point="gymnasium:gymnasium.wrappers.AutoResetWrapper",
                kwargs={},
            ),
        ),
    )

- It is no longer recommended to use `Space.sample()
  <gymnasium.spaces.space.Space.sample>` to generate random actions,
  observations or parameters if deterministic and reproducible behavior is
  desired. Instead, all random numbers should be sourced from :ref:`the new
  environment-exclusive generator <guide/migration_090:Changes to Environment
  Reseeding>`. Keep in mind all warnings in the dedicated section.

- The function :func:`gymnasium.vector.make()` has been deprecated in favor of
  :func:`gymnasium.make_vec()`. The API for vector environments is still
  subject to change and currently available as
  `gymnasium.experimental.vector.VectorEnv`.

To summarize the deprecated and new constructs:

=========================================   ================================================
Deprecated behavior                         Recommended instead
=========================================   ================================================
:samp:`{wrapped}.{env_attr}`                :samp:`{wrapped}.get_wrapper_attr("{env_attr}")`
:samp:`\\{"render.modes": {modes}\\}`       :samp:`\\{"render_modes": {modes}\\}`
:samp:`self.reward_range=({low}, {high})`   —
:samp:`make({env_id}, autoreset=True)`      *See above*
:samp:`self.observation_space.sample()`     :samp:`self.np_random.uniform({low}, {high})`
:samp:`vector.make({*args})`                :samp:`make_vec({*args})`
=========================================   ================================================
