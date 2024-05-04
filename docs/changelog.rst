..
    SPDX-FileCopyrightText: 2020-2024 CERN
    SPDX-FileCopyrightText: 2023-2024 GSI Helmholtzzentrum für Schwerionenforschung
    SPDX-FileNotice: All rights not expressly granted are reserved.

    SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

Changelog
=========

.. currentmodule:: cernml.coi

.. _semantic-versioning:

This package uses a variant of `Semantic Versioning <https://semver.org/>`_
that makes additional promises during the initial development (major version
0): whenever breaking changes to the public API are published, the first
non-zero version number will increase. This means that code that uses COI
version 0.8.10 will continue to work with version 0.8.11, but may break with
version 0.9.0.

Unreleased
----------

.. seealso::

    :doc:`guide/migration_090`
        User guide page listing all breaking changes and how to adapt your
        code.

- BREAKING: Require Python 3.9.
- BREAKING: Switched dependency from Gym 0.21 to Gymnasium.
- BREAKING: Update NumPy requirement from 1.0 to 1.22.
- BREAKING: Update optional Matplotlib requirement from 3.0 to 3.8.
- BREAKING: Update optional cernml-coi-optimizers requirement from 1.1 to 2.0.
- BREAKING: Update built-time setuptools-scm requirement from 7.0 to 8.
- BREAKING: Update :doc:`importlib-metadata <importlib_metadata:index>` from
  ``< 7`` to ``>= 4.8``.
- BREAKING: Add dependency on ``typing-extensions >= 4.3``.
- BREAKING: The `~Problem.metadata` key ``"render.modes"`` has been renamed to
  :mdkey:`"render_modes"`. Its meaning has not changed.
- BREAKING: New rendering API: `Problem.render()` now longer accepts the
  arguments *render_mode*. This argument is now instead passed to
  `Problem.__init__() <Problem>`, which automatically sets the new property
  `Problem.render_mode`. In rendering mode :rmode:`"human"`, problems are now
  expected to call `~Problem.render()` automatically at every iteration.
- BREAKING: `SingleOptimizable.get_initial_params()`,
  `FunctionOptimizable.get_initial_params()` and `Env.reset()
  <gymnasium.Env.reset>` now accept new arguments *seed* and *options*. The
  latter is ignored by default, the former is used to seed the new property
  `Problem.np_random`.
- BREAKING: The convention around the return value of
  `~SingleOptimizable.get_initial_params()` has been clarified. Unless and
  until a new API has been worked out, its return value must now be accepted by
  `~SingleOptimizable.compute_single_objective()` and
  `~FunctionOptimizable.compute_function_objective()` even if its
  out-of-bounds.
- BREAKING: The :doc:`api/classes` have been completely rewritten. Instance and
  subclass checks are now based on the `Protocol` implementation from Python
  3.12. Dynamically set attributes may no longer be found and checks now also
  consider whether an attribute is a data member, a method or a class method.
- BREAKING: The entry point used by the :doc:`api/checkers` has been renamed
  from ``cernml.coi.checkers`` to :ep:`cernml.checkers`.
- BREAKING: The attributes ``SingleOptimizable.objective_range`` and
  ``FunctionOptimizable.objective_range`` have been removed in anticipation of
  `the planned removal
  <https://github.com/Farama-Foundation/Gymnasium/pull/535>`_ of
  `gymnasium.Env.reward_range` in Gymnasium 1.0.
- ADD: Support for Python 3.10 through 3.12.
- ADD: New extra ``robotics``, which adds a dependency on
  :doc:`Gymnasium-Robotics <gymrob:README>` 1.0 and sources `GoalEnv` from
  there.
- ADD: If :doc:`Gymnasium-Robotics <gymrob:README>` isn't installed, we provide
  our own implementation of `cernml.coi.GoalEnv`.
- New entry point :ep:`cernml.envs` through which :ref:`problems can be
  registered <guide/registration:lazy registration via entry points>`.
- ADD: The *warn* parameter of the :doc:`api/checkers` now is an integer
  instead of a bool. The meaning stays largely the same. Values greater than
  2 now represent the *stacklevel* parameter passed to :func:`warnings.warn()`
  to adjust the reported code location when a warning is issued. Internally,
  the checkers adjust *warn* so that warnings are never reported within the
  :doc:`api/checkers` package itself.
- ADD: A large family of :doc:`api/typeguards` to require that an instance or
  class implement a specific interface.
- ADD: The :doc:`api/classes` are now all context managers; entering their
  context does nothing, leaving it calls `Problem.close()`.
- ADD: The method `Problem.get_wrapper_attr()`.
- FIX: For `FunctionOptimizable`, the type of the
  `~FunctionOptimizable.constraints` attribute has been changed from `List` to
  `Sequence`. It has also been marked as a `typing.ClassVar` and the default
  value has been changed from the empty list ``[]`` to the empty tuple ``()``.
  The same has been done in `SingleOptimizable` for its attributes
  `~SingleOptimizable.param_names`, `~SingleOptimizable.constraints`, and
  `~SingleOptimizable.constraint_names` This prevents bugs where the default
  values are modified on accident. A similar strategy has long been used for
  the `~Problem.metadata` attribute.
- OTHER: :doc:`api/registration` has been rewritten from scratch. It still
  largely follows the :doc:`Gymnasium implementation <gym:api/registry>` and
  should be backwards-compatible, but minor details may have changed
  inadvertently.

v0.8
----

v0.8.16
^^^^^^^

- ADD: `~cernml.coi.CustomPolicyProvider` and a :ref:`user guide section
  <guide/custom_optimizers:Custom Per-Environment Policies>` about it.

v0.8.15
^^^^^^^

- ADD: `CustomOptimizerProvider` and a :doc:`user guide section
  <guide/custom_optimizers>` about it.
- ADD: A :doc:`user guide section <guide/configurable>` on the `Configurable`
  API.

v0.8.14
^^^^^^^

- ADD: `Config.add() <Config.add()>` now has a different default value for the
  *type* parameter in cases where *value* is a `bool` or `numpy.bool_`. The new
  value treats most inputs as before, but specifically the string ``"False"``
  is converted to the boolean `False` of the correct type. This ensures that
  bools roundtrip through string conversion and makes config handling in host
  applications less error-prone.
- FIX: The :doc:`/api/checkers` now run their :func:`isinstance()` checks on
  the `~Problem.unwrapped` optimization problem instead of the problem itself.
  This solves a bug where a `SingleOptimizable` inside a `~gymnasium.Wrapper`
  is mistaken for an `~gymnasium.Env`.
- FIX: Add missing argument *order_enforce* to `~register()` for compatibility
  with the equivalent Gym function.

v0.8.13
^^^^^^^

- FIX: Add compatibility with :doc:`importlib-metadata
  <importlib_metadata:index>` 5 and 6 *if* we're on Python 3.8+. On Python 3.7
  (Acc-Py 2020.11), we are still forced to use importlib-metadata 4.

v0.8.12
^^^^^^^

- FIX: Bad CI configuration that prevented the package from being released.

v0.8.11
^^^^^^^

- FIX: Bad CI configuration that prevented docs from being built.

v0.8.10
^^^^^^^

- FIX: Improve cross-linking in the docs.
- FIX: Update packaging tutorial to latest version of tools.
- FIX: General small rewrite of the docs.
- OTHER: Documentation previously written in Markdown is now consistently
  written in ReST.
- OTHER: Open-source this package by adding the appropriate license notices.

v0.8.9
^^^^^^

- ADD: :meth:`~FunctionOptimizable.override_skeleton_points()` for optimization
  problems that need to customize the way skeleton points are selected by the
  user.
- OTHER: The online docs are now built with Python 3.9. Consequently, type
  annotations like ``Union[str, List[str]]`` and ``Optional[str]`` now use the
  new `type union syntax
  <https://docs.python.org/3/whatsnew/3.10.html#pep-604-new-type-union-operator>`_
  added in Python 3.10, and so look like ``str | List[str]`` and ``str | None``
  respectively.

v0.8.8
^^^^^^

- FIX: Improve various cross-references in the docs.
- OTHER: The project's Gitlab group has been renamed from
  *be-op-ml-optimization* to *geoff*. This also changes the URL of these docs
  inside CERN. Please adjust your links, bookmarks and Git clones.

v0.8.7
^^^^^^

- ADD: Support for Python 3.9 has been added.
- FIX: Do not require Matplotlib/PyJapc to build documentation
- FIX: Drop the install extra "pyjapc".
- OTHER: Bump build dependencies.
- OTHER: Switch project layout to src-based and migrate almost all configs to
  pyproject.toml.

v0.8.6
^^^^^^

- ADD: :meth:`Config.get_field_values()` for convenience.

v0.8.5
^^^^^^

- ADD: Variants ``AD`` and ``ELENA`` to enum :class:`Machine`.

v0.8.4
^^^^^^

- FIX: Change syntax highlighter for shell sessions in docs from ``bash`` to
  ``shell-session``.
- OTHER: Upgrade CI templates to v2.
- OTHER: Use Gitlab Releases and Gitlab badges.
- OTHER: Add key ``project_urls`` to setup.cfg.

v0.8.3
^^^^^^

- ADD: Add install extra ``doc_only`` to build docs in a non-CERN environment.
  (This skips the PyJapc dependency.)
- FIX: Restrict Gym compatibility, as `Gym v0.22
  <https://github.com/openai/gym/releases/tag/0.22.0>`_ removes
  :class:`.GoalEnv`.
- FIX: :ref:`changelog:v0.8.0` nominally increased the minimum required version
  of :doc:`importlib-metadata <importlib_metadata:index>`, but this was never
  enforced. Now, at least version 3.6 is required.

v0.8.2
^^^^^^

- ADD: New optional attributes :attr:`~SingleOptimizable.objective_name`,
  :attr:`~SingleOptimizable.param_names` and
  :attr:`~SingleOptimizable.constraint_names` to :class:`SingleOptimizable`.
- FIX: Adjust the documentation of
  :meth:`~FunctionOptimizable.get_objective_function_name()` and
  :meth:`~FunctionOptimizable.get_param_function_names()` to be in line with
  its :class:`SingleOptimizable` counter-parts.

v0.8.1
^^^^^^

- ADD: :meth:`Config.extend()` to make configuration more composable.
- ADD: :class:`ConfigValues` as a convenience alias for
  :class:`types.SimpleNamespace`.
- ADD: :func:`~checkers.check_configurable()` for all implementors of the
  :class:`Configurable` interface.
- FIX: Broken links in the API docs of the :doc:`api/checkers`.

v0.8.0
^^^^^^

- BREAKING: Drop Python 3.6 support.
- BREAKING: Require :doc:`importlib-metadata <importlib_metadata:index>` 3.6
  (was 3.4).
- BREAKING: Drop the ``__version__`` attribute. To query the COI version, use
  instead :mod:`importlib_metadata`. (With Python 3.8+, this is in the standard
  library as :mod:`importlib.metadata`.)
- BREAKING: Remove ``PascalPase``-style members of :class:`Machine`. Use the
  ``SCREAMING_SNAKE_CASE``-style members intead.
- BREAKING: Remove ``unstable.japc_utils``. It is now provided by
  :doc:`cernml-coi-utils <utils:index>` as :mod:`cernml.japc_utils`.
- BREAKING: Remove ``unstable.renderer`` and ``mpl_utils``. Both are now
  provided by :doc:`cernml-coi-utils <utils:index>`'s :mod:`cernml.mpl_utils`.
- BREAKING: Remove ``unstable.cancellation``. The module is now available as
  :mod:`cernml.coi.cancellation`.
- BREAKING: Remove ``unstable``. The module is now empty.
- BREAKING: Change :class:`~Config.Field` from a :class:`~typing.NamedTuple`
  into a :func:`~dataclasses.dataclass`.
- ADD: Support for :doc:`importlib-metadata<importlib_metadata:index>` 4.

v0.7
----

v0.7.6
^^^^^^

- FIX: Backport change from v0.8.x that removes
  :func:`~cernml.mpl_utils.iter_matplotlib_figures()` calls from
  :func:`check()`. This avoids deprecation warnings introduced in the previous
  version.

v0.7.5
^^^^^^

- FIX: Increase the stacklevel of the :ref:`changelog:v0.7.4` deprecation
  warnings so that they appear more reliably.

v0.7.4
^^^^^^

- ADD: Merge :class:`FunctionOptimizable` and
  :func:`~checkers.check_function_optimizable()` from cernml-coi-funcs v0.2.2.
- ADD: Deprecate ``unstable.japc_utils``, :doc:`renderer<utils:api/mpl_utils>`
  and :doc:`mpl_utils<utils:api/mpl_utils>`. The same features are provided by
  the :doc:`cernml-coi-utils<utils:index>` package.
- ADD: Stabilize the :mod:`cernml.coi.cancellation` module. It is now available
  under ``cancellation``. The old location at ``unstable.cancellation`` remains
  available but is deprecated.
- FIX: Correct the type annotation on
  :class:`~SingleOptimizable.get_initial_params()` from :data:`~std:typing.Any`
  to :class:`~np:numpy.ndarray`.

v0.7.3
^^^^^^

- ADD: Split the COI tutorial into a :doc:`tutorial on packaging
  <tutorials/packaging>` and a :doc:`tutorial on the COI proper
  <tutorials/implement-singleoptimizable>`.
- FIX: Improve the documentation of :class:`Env` and other Gym classes.
- OTHER: Upgraded docs. Switch markdown parser from Recommonmark to Myst.
  Change theme from *Read the Docs* to *Sphinxdoc*.
- OTHER: Changes to the CI pipeline. Version of code checkers are pinned now.
  Added Pycodestyle to the list of checkers to run.

v0.7.2
^^^^^^

- ADD: :meth:`ParamStream.next_if_ready()
  <cernml.japc_utils.ParamStream.pop_if_ready()>` no longer checks stream's the
  cancellation token.
- ADD: :attr:`ParamStream.parameter_name
  <cernml.japc_utils.ParamStream.parameter_name>` and
  :attr:`ParamGroupStream.parameter_names
  <cernml.japc_utils.ParamGroupStream.parameter_names>`.
- FIX: :func:`repr()` of :class:`~cernml.japc_utils.ParamGroupStream` called
  wrong Java API.

v0.7.1
^^^^^^

- ADD: Enum member :attr:`Machine.ISOLDE <Machine.ISOLDE>`.

v0.7.0
^^^^^^

- BREAKING: Remove :ref:`Cancellation tokens
  <guide/cancellation:Cancellation>`. The stable API did not accommodate all
  required use cases and could not be fixed in a backwards-compatible manner.
- ADD: Re-add :ref:`Cancellation tokens <guide/cancellation:Cancellation>` as
  an unstable module. The new API supports cancellation completion and resets.

v0.6
----

v0.6.2
^^^^^^

- ADD: Rename all variants of :class:`Machine` to ``SCREAMING_SNAKE_CASE``. The
  ``PascalCase`` names remain available, but issue a deprecation warning.
- ADD: :ref:`Cancellation tokens <guide/cancellation:Cancellation>`.
- ADD: Cancellation support to :func:`parameter streams
  <cernml.japc_utils.subscribe_stream>`.
- ADD: Property :attr:`~cernml.japc_utils.ParamStream.locked` to parameter
  streams.
- ADD: Document :ref:`parameter streams <guide/cancellation:Synchronization>`.
- ADD: Document plugin support in :func:`check`.
- FIX: Add default values for all known :attr:`~Problem.metadata` keys.
- FIX: Missing ``figure.show()`` when calling
  :meth:`SimpleRenderer.update("human") <cernml.mpl_utils.Renderer.update>`.

v0.6.1
^^^^^^

- ADD: *title* parameter to :meth:`SimpleRenderer.from_generator()
  <cernml.mpl_utils.FigureRenderer.from_callback>`.
- FIX: Missing ``figure.draw()`` when calling
  :meth:`SimpleRenderer.update("human") <cernml.mpl_utils.Renderer.update>`.

v0.6.0
^^^^^^

- BREAKING: Instate :ref:`a variant of semantic versioning
  <semantic-versioning>`.
- BREAKING: Move the :doc:`Matplotlib utilities <utils:api/mpl_utils>` into
  ``mpl_utils``.
- ADD: :class:`unstable.renderer <cernml.mpl_utils.Renderer>`.
- ADD: :mod:`unstable.japc_utils <cernml.japc_utils>`.
- ADD: Allow a single :class:`~matplotlib.figure.Figure` as return value of
  :meth:`render("matplotlib_figure") <Problem.render>`.

v0.5
----

v0.5.0
^^^^^^

- BREAKING: Add :meth:`Problem.close`.

v0.4
----

v0.4.7
^^^^^^

- FIX: Typo in :attr:`~Problem.metadata` key :mdkey:`"cern.machine"`.
- FIX: Mark :attr:`~Problem.metadata` as a class variable.
- FIX: Make base :attr:`~Problem.metadata` a :class:`~types.MappingProxyType`
  to prevent accidental mutation.

v0.4.6
^^^^^^

- BREAKING: Remove keyword arguments from the signature of
  :meth:`~Problem.render`.
- ADD: Start distributing wheels.

v0.4.5
^^^^^^

- ADD: Plugin entry point and logging to :func:`check()`.

v0.4.4
^^^^^^

- ADD: Export some (for now) undocumented helper functions from
  `checkers<check>`.

v0.4.3
^^^^^^

- BREAKING: Switch to setuptools-scm for versioning.
- ADD: Unmark :meth:`~Problem.render` as an abstract method.

v0.4.2
^^^^^^

- ADD: Make dependency on Matplotlib optional.
- FIX: Add missing check for defined render modes to :func:`check()`.

v0.4.1
^^^^^^

- FIX: Expose :func:`check()` argument *headless*.

v0.4.0
^^^^^^

- BREAKING: Mark the package as fully type-annotated.
- BREAKING: Switch to pyproject.toml and setup.cfg based building.
- BREAKING: Rewrite ``check_env()`` as :func:`check()`.
- ADD: :func:`mpl_utils.iter_matplotlib_figures()
  <cernml.mpl_utils.iter_matplotlib_figures>`.

v0.3
----

v0.3.3
^^^^^^

- FIX: Set window title in example ``configurable.py``.

v0.3.2
^^^^^^

- ADD: *help* argument to :meth:`Config.add()`.

v0.3.1
^^^^^^

- BREAKING: Make all submodules private.
- ADD: :class:`Configurable` interface.

v0.3.0
^^^^^^

- BREAKING: Rename ``Optimizable`` to :class:`SingleOptimizable`.
- BREAKING: Add dependency on Numpy.
- ADD: :class:`Problem` interface.
- ADD: :doc:`Environment registry<api/registration>`.
- FIX: Check inheritance of :attr:`env.unwrapped<Problem.unwrapped>` in
  :func:`check_env()<check>`.

v0.2
----

v0.2.1
^^^^^^

- FIX: Fix broken CI tests.

v0.2.0
^^^^^^

- BREAKING: Rename package from ``cernml.abc`` to ``cernml.coi`` (And the
  distribution from ``cernml-abc`` to ``cernml-coi``).
- BREAKING: Rename ``OptimizeMixin`` to
  :class:`Optimizable<SingleOptimizable>`.
- BREAKING: Add :attr:`~Problem.metadata` key :mdkey:`"cern.machine"`.
- BREAKING: Add more restrictions to :func:`env_checker()<check>`.
- ADD: Virtual inheritance: Any class that implements the required methods of
  our interfaces automatically subclass them, even if they are not direct
  bases.
- FIX: Make :class:`SeparableOptEnv` subclass :class:`SeparableEnv`.

v0.1
----

v0.1.0
^^^^^^

The dawn of time.
