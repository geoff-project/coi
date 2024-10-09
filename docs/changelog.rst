.. SPDX-FileCopyrightText: 2020 - 2024 CERN
.. SPDX-FileCopyrightText: 2023 - 2024 GSI Helmholtzzentrum für Schwerionenforschung
.. SPDX-FileNotice: All rights not expressly granted are reserved.
..
.. SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

:tocdepth: 3

Changelog
=========

.. currentmodule:: cernml.coi

.. _semantic-versioning:

This package uses a variant of `Semantic Versioning <https://semver.org/>`_
that makes additional promises during the initial development (major version
0): whenever breaking changes to the public API are published, the first
non-zero version number will increase. This means that code that uses COI
version 0.9.0 will continue to work with version 0.9.1, but may break with
version 0.10.0.

Unreleased
----------

No changes yet!

v0.9.2
^^^^^^

Bug fixes
~~~~~~~~~
- Fix superfluous warnings in `cernml.coi.checkers.check_problem()` when
  looking for deprecated attributes.
- The function `cernml.coi.check()` now loads all plugins first before
  executing them. It also logs faulty plugins, but otherwise ignores them. This
  should catch bugs quicker.

v0.9
----

.. seealso::

    :doc:`guide/migration_090`
        User guide page listing all breaking changes and how to adapt your
        code.

v0.9.1
^^^^^^

Bug fixes
~~~~~~~~~
- Relax dependencies to allow use of NumPy 2.0
- Fix bug in which building the docs would fail due to double slashes in the
  URLs of other package documentations.

v0.9.0
^^^^^^

Breaking changes
~~~~~~~~~~~~~~~~
- Require Python 3.9.
- Switched dependency from Gym 0.21 to Gymnasium.
- Update NumPy requirement from 1.0 to 1.22.
- Update optional Matplotlib requirement from 3.0 to 3.8.
- Update optional cernml-coi-optimizers requirement from 1.1 to 2.0.
- Update built-time setuptools-scm requirement from 7.0 to 8.
- Update :doc:`importlib-metadata <importlib_metadata:index>` from
  ``< 7`` to ``>= 4.8``.
- Add dependency on ``typing-extensions >= 4.3``.
- The `~Problem.metadata` key ``"render.modes"`` has been renamed to
  :mdkey:`"render_modes"`. Its meaning has not changed.
- New rendering API: `Problem.render()` now longer accepts the
  arguments *render_mode*. This argument is now instead passed to
  `Problem.__init__() <Problem>`, which automatically sets the new property
  `Problem.render_mode`. In rendering mode :rmode:`"human"`, problems are now
  expected to call `~Problem.render()` automatically at every iteration.
- `SingleOptimizable.get_initial_params()`,
  `FunctionOptimizable.get_initial_params()` and `Env.reset()
  <gymnasium.Env.reset>` now accept new arguments *seed* and *options*. The
  latter is ignored by default, the former is used to seed the new property
  `Problem.np_random`.
- The convention around the return value of
  `~SingleOptimizable.get_initial_params()` has been clarified. Unless and
  until a new API has been worked out, its return value must now be accepted by
  `~SingleOptimizable.compute_single_objective()` and
  `~FunctionOptimizable.compute_function_objective()` even if its
  out-of-bounds.
- The :doc:`api/classes` have been completely rewritten. Instance and
  subclass checks are now based on the `Protocol` implementation from Python
  3.12. Dynamically set attributes may no longer be found and checks now also
  consider whether an attribute is a data member, a method or a class method.
- The entry point used by the :doc:`api/checkers` has been renamed
  from ``cernml.coi.checkers`` to :ep:`cernml.checkers`.
- The attributes ``SingleOptimizable.objective_range`` and
  ``FunctionOptimizable.objective_range`` have been removed in anticipation of
  `the planned removal
  <https://github.com/Farama-Foundation/Gymnasium/pull/535>`_ of
  `gymnasium.Env.reward_range` in Gymnasium 1.0.

Additions
~~~~~~~~~
- Support for Python 3.10 through 3.12.
- New extra ``robotics``, which adds a dependency on
  :doc:`Gymnasium-Robotics <gymrob:README>` 1.0 and sources `GoalEnv` from
  there.
- If :doc:`Gymnasium-Robotics <gymrob:README>` isn't installed, we provide
  our own implementation of `cernml.coi.GoalEnv`.
- New entry point :ep:`cernml.envs` through which :ref:`problems can be
  registered <guide/registration:lazy registration via entry points>`.
- The *warn* parameter of the :doc:`api/checkers` now is an integer
  instead of a bool. The meaning stays largely the same. Values greater than
  2 now represent the *stacklevel* parameter passed to :func:`warnings.warn()`
  to adjust the reported code location when a warning is issued. Internally,
  the checkers adjust *warn* so that warnings are never reported within the
  :doc:`api/checkers` package itself.
- A large family of :doc:`api/typeguards` to require that an instance or
  class implement a specific interface.
- The :doc:`api/classes` are now all context managers; entering their
  context does nothing, leaving it calls `Problem.close()`.
- The method `Problem.get_wrapper_attr()`.

Bug fixes
~~~~~~~~~
- For `FunctionOptimizable`, the type of the
  `~FunctionOptimizable.constraints` attribute has been changed from `List` to
  `Sequence`. It has also been marked as a `typing.ClassVar` and the default
  value has been changed from the empty list ``[]`` to the empty tuple ``()``.
  The same has been done in `SingleOptimizable` for its attributes
  `~SingleOptimizable.param_names`, `~SingleOptimizable.constraints`, and
  `~SingleOptimizable.constraint_names` This prevents bugs where the default
  values are modified on accident. A similar strategy has long been used for
  the `~Problem.metadata` attribute.

Other changes
~~~~~~~~~~~~~
- :doc:`api/registration` has been rewritten from scratch. It still
  largely follows the :doc:`Gymnasium implementation <gym:api/registry>` and
  should be backwards-compatible, but minor details may have changed
  inadvertently.

v0.8
----

v0.8.16
^^^^^^^

Additions
~~~~~~~~~
- `~cernml.coi.CustomPolicyProvider` and a :ref:`user guide section
  <guide/custom_optimizers:Custom Per-Environment Policies>` about it.

v0.8.15
^^^^^^^

- `CustomOptimizerProvider` and a :doc:`user guide section
  <guide/custom_optimizers>` about it.
- A :doc:`user guide section <guide/configurable>` on the `Configurable`
  API.

v0.8.14
^^^^^^^

Additions
~~~~~~~~~
- `Config.add() <Config.add()>` now has a different default value for the
  *type* parameter in cases where *value* is a `bool` or `numpy.bool_`. The new
  value treats most inputs as before, but specifically the string ``"False"``
  is converted to the boolean `False` of the correct type. This ensures that
  bools roundtrip through string conversion and makes config handling in host
  applications less error-prone.

Bug fixes
~~~~~~~~~
- The :doc:`/api/checkers` now run their :func:`isinstance()` checks on
  the `~Problem.unwrapped` optimization problem instead of the problem itself.
  This solves a bug where a `SingleOptimizable` inside a `~gymnasium.Wrapper`
  is mistaken for an `~gymnasium.Env`.
- Add missing argument *order_enforce* to `~register()` for compatibility
  with the equivalent Gym function.

v0.8.13
^^^^^^^

Bug fixes
~~~~~~~~~
- Add compatibility with :doc:`importlib-metadata
  <importlib_metadata:index>` 5 and 6 *if* we're on Python 3.8+. On Python 3.7
  (Acc-Py 2020.11), we are still forced to use importlib-metadata 4.

v0.8.12
^^^^^^^

Bug fixes
~~~~~~~~~
- Bad CI configuration that prevented the package from being released.

v0.8.11
^^^^^^^

Bug fixes
~~~~~~~~~
- Bad CI configuration that prevented docs from being built.

v0.8.10
^^^^^^^

Bug fixes
~~~~~~~~~
- Improve cross-linking in the docs.
- Update packaging tutorial to latest version of tools.
- General small rewrite of the docs.

Other changes
~~~~~~~~~~~~~
- Documentation previously written in Markdown is now consistently
  written in ReST.
- Open-source this package by adding the appropriate license notices.

v0.8.9
^^^^^^

Additions
~~~~~~~~~
- :meth:`~FunctionOptimizable.override_skeleton_points()` for optimization
  problems that need to customize the way skeleton points are selected by the
  user.

Other changes
~~~~~~~~~~~~~
- The online docs are now built with Python 3.9. Consequently, type
  annotations like ``Union[str, List[str]]`` and ``Optional[str]`` now use the
  new `type union syntax
  <https://docs.python.org/3/whatsnew/3.10.html#pep-604-new-type-union-operator>`_
  added in Python 3.10, and so look like ``str | List[str]`` and ``str | None``
  respectively.

v0.8.8
^^^^^^

Bug fixes
~~~~~~~~~
- Improve various cross-references in the docs.

Other changes
~~~~~~~~~~~~~
- The project's Gitlab group has been renamed from
  *be-op-ml-optimization* to *geoff*. This also changes the URL of these docs
  inside CERN. Please adjust your links, bookmarks and Git clones.

v0.8.7
^^^^^^

Additions
~~~~~~~~~
- Support for Python 3.9 has been added.

Bug fixes
~~~~~~~~~
- Do not require Matplotlib/PyJapc to build documentation
- Drop the install extra "pyjapc".

Other changes
~~~~~~~~~~~~~
- Bump build dependencies.
- Switch project layout to src-based and migrate almost all configs to
  pyproject.toml.

v0.8.6
^^^^^^

Additions
~~~~~~~~~
- :meth:`Config.get_field_values()` for convenience.

v0.8.5
^^^^^^

Additions
~~~~~~~~~
- Variants ``AD`` and ``ELENA`` to enum :class:`Machine`.

v0.8.4
^^^^^^

Bug fixes
~~~~~~~~~
- Change syntax highlighter for shell sessions in docs from ``bash`` to
  ``shell-session``.

Other changes
~~~~~~~~~~~~~
- Upgrade CI templates to v2.
- Use Gitlab Releases and Gitlab badges.
- Add key ``project_urls`` to setup.cfg.

v0.8.3
^^^^^^

Additions
~~~~~~~~~
- Add install extra ``doc_only`` to build docs in a non-CERN environment.
  (This skips the PyJapc dependency.)

Bug fixes
~~~~~~~~~
- Restrict Gym compatibility, as `Gym v0.22
  <https://github.com/openai/gym/releases/tag/0.22.0>`_ removes
  :class:`.GoalEnv`.
- :ref:`changelog:v0.8.0` nominally increased the minimum required version
  of :doc:`importlib-metadata <importlib_metadata:index>`, but this was never
  enforced. Now, at least version 3.6 is required.

v0.8.2
^^^^^^

Additions
~~~~~~~~~
- New optional attributes :attr:`~SingleOptimizable.objective_name`,
  :attr:`~SingleOptimizable.param_names` and
  :attr:`~SingleOptimizable.constraint_names` to :class:`SingleOptimizable`.

Bug fixes
~~~~~~~~~
- Adjust the documentation of
  :meth:`~FunctionOptimizable.get_objective_function_name()` and
  :meth:`~FunctionOptimizable.get_param_function_names()` to be in line with
  its :class:`SingleOptimizable` counter-parts.

v0.8.1
^^^^^^

Additions
~~~~~~~~~
- :meth:`Config.extend()` to make configuration more composable.
- :class:`ConfigValues` as a convenience alias for
  :class:`types.SimpleNamespace`.
- :func:`~checkers.check_configurable()` for all implementors of the
  :class:`Configurable` interface.

Bug fixes
~~~~~~~~~
- Broken links in the API docs of the :doc:`api/checkers`.

v0.8.0
^^^^^^

Breaking changes
~~~~~~~~~~~~~~~~
- Drop Python 3.6 support.
- Require :doc:`importlib-metadata <importlib_metadata:index>` 3.6
  (was 3.4).
- Drop the ``__version__`` attribute. To query the COI version, use
  instead :mod:`importlib_metadata`. (With Python 3.8+, this is in the standard
  library as :mod:`importlib.metadata`.)
- Remove ``PascalPase``-style members of :class:`Machine`. Use the
  ``SCREAMING_SNAKE_CASE``-style members intead.
- Remove ``unstable.japc_utils``. It is now provided by
  :doc:`cernml-coi-utils <utils:index>` as :mod:`cernml.japc_utils`.
- Remove ``unstable.renderer`` and ``mpl_utils``. Both are now
  provided by :doc:`cernml-coi-utils <utils:index>`'s :mod:`cernml.mpl_utils`.
- Remove ``unstable.cancellation``. The module is now available as
  :mod:`cernml.coi.cancellation`.
- Remove ``unstable``. The module is now empty.
- Change :class:`~Config.Field` from a :class:`~typing.NamedTuple`
  into a :func:`~dataclasses.dataclass`.

Additions
~~~~~~~~~
- Support for :doc:`importlib-metadata<importlib_metadata:index>` 4.

v0.7
----

v0.7.6
^^^^^^

Bug fixes
~~~~~~~~~
- Backport change from v0.8.x that removes
  :func:`~cernml.mpl_utils.iter_matplotlib_figures()` calls from
  :func:`check()`. This avoids deprecation warnings introduced in the previous
  version.

v0.7.5
^^^^^^

Bug fixes
~~~~~~~~~
- Increase the stacklevel of the :ref:`changelog:v0.7.4` deprecation
  warnings so that they appear more reliably.

v0.7.4
^^^^^^

Additions
~~~~~~~~~
- Merge :class:`FunctionOptimizable` and
  :func:`~checkers.check_function_optimizable()` from cernml-coi-funcs v0.2.2.
- Deprecate ``unstable.japc_utils``, :doc:`renderer<utils:api/mpl_utils>`
  and :doc:`mpl_utils<utils:api/mpl_utils>`. The same features are provided by
  the :doc:`cernml-coi-utils<utils:index>` package.
- Stabilize the :mod:`cernml.coi.cancellation` module. It is now available
  under ``cancellation``. The old location at ``unstable.cancellation`` remains
  available but is deprecated.

Bug fixes
~~~~~~~~~
- Correct the type annotation on
  :class:`~SingleOptimizable.get_initial_params()` from :data:`~std:typing.Any`
  to :class:`~np:numpy.ndarray`.

v0.7.3
^^^^^^

Additions
~~~~~~~~~
- Split the COI tutorial into a :doc:`tutorial on packaging
  <tutorials/packaging>` and a :doc:`tutorial on the COI proper
  <tutorials/implement-singleoptimizable>`.

Bug fixes
~~~~~~~~~
- Improve the documentation of :class:`Env` and other Gym classes.

Other changes
~~~~~~~~~~~~~
- Upgraded docs. Switch markdown parser from Recommonmark to Myst.
  Change theme from *Read the Docs* to *Sphinxdoc*.
- Changes to the CI pipeline. Version of code checkers are pinned now.
  Added Pycodestyle to the list of checkers to run.

v0.7.2
^^^^^^

Additions
~~~~~~~~~
- :meth:`ParamStream.next_if_ready()
  <cernml.japc_utils.ParamStream.pop_if_ready()>` no longer checks stream's the
  cancellation token.
- :attr:`ParamStream.parameter_name
  <cernml.japc_utils.ParamStream.parameter_name>` and
  :attr:`ParamGroupStream.parameter_names
  <cernml.japc_utils.ParamGroupStream.parameter_names>`.

Bug fixes
~~~~~~~~~
- :func:`repr()` of :class:`~cernml.japc_utils.ParamGroupStream` called
  wrong Java API.

v0.7.1
^^^^^^

Additions
~~~~~~~~~
- Enum member :attr:`Machine.ISOLDE <Machine.ISOLDE>`.

v0.7.0
^^^^^^

Breaking changes
~~~~~~~~~~~~~~~~
- Remove :ref:`Cancellation tokens
  <guide/cancellation:Cancellation>`. The stable API did not accommodate all
  required use cases and could not be fixed in a backwards-compatible manner.

Additions
~~~~~~~~~
- Re-add :ref:`Cancellation tokens <guide/cancellation:Cancellation>` as
  an unstable module. The new API supports cancellation completion and resets.

v0.6
----

v0.6.2
^^^^^^

Additions
~~~~~~~~~
- Rename all variants of :class:`Machine` to ``SCREAMING_SNAKE_CASE``. The
  ``PascalCase`` names remain available, but issue a deprecation warning.
- :ref:`Cancellation tokens <guide/cancellation:Cancellation>`.
- Cancellation support to :func:`parameter streams
  <cernml.japc_utils.subscribe_stream>`.
- Property :attr:`~cernml.japc_utils.ParamStream.locked` to parameter
  streams.
- Document :ref:`parameter streams <guide/cancellation:Synchronization>`.
- Document plugin support in :func:`check`.

Bug fixes
~~~~~~~~~
- Add default values for all known :attr:`~Problem.metadata` keys.
- Missing ``figure.show()`` when calling
  :meth:`SimpleRenderer.update("human") <cernml.mpl_utils.Renderer.update>`.

v0.6.1
^^^^^^

Additions
~~~~~~~~~
- *title* parameter to :meth:`SimpleRenderer.from_generator()
  <cernml.mpl_utils.FigureRenderer.from_callback>`.

Bug fixes
~~~~~~~~~
- Missing ``figure.draw()`` when calling
  :meth:`SimpleRenderer.update("human") <cernml.mpl_utils.Renderer.update>`.

v0.6.0
^^^^^^

Breaking changes
~~~~~~~~~~~~~~~~
- Instate :ref:`a variant of semantic versioning
  <semantic-versioning>`.
- Move the :doc:`Matplotlib utilities <utils:api/mpl_utils>` into
  ``mpl_utils``.

Additions
~~~~~~~~~
- :class:`unstable.renderer <cernml.mpl_utils.Renderer>`.
- :mod:`unstable.japc_utils <cernml.japc_utils>`.
- Allow a single :class:`~matplotlib.figure.Figure` as return value of
  :meth:`render("matplotlib_figure") <Problem.render>`.

v0.5
----

v0.5.0
^^^^^^

Breaking changes
~~~~~~~~~~~~~~~~
- Add :meth:`Problem.close`.

v0.4
----

v0.4.7
^^^^^^

Bug fixes
~~~~~~~~~
- Typo in :attr:`~Problem.metadata` key :mdkey:`"cern.machine"`.
- Mark :attr:`~Problem.metadata` as a class variable.
- Make base :attr:`~Problem.metadata` a :class:`~types.MappingProxyType`
  to prevent accidental mutation.

v0.4.6
^^^^^^

Breaking changes
~~~~~~~~~~~~~~~~
- Remove keyword arguments from the signature of
  :meth:`~Problem.render`.

Additions
~~~~~~~~~
- Start distributing wheels.

v0.4.5
^^^^^^

Additions
~~~~~~~~~
- Plugin entry point and logging to :func:`check()`.

v0.4.4
^^^^^^

Additions
~~~~~~~~~
- Export some (for now) undocumented helper functions from
  `checkers<check>`.

v0.4.3
^^^^^^

Breaking changes
~~~~~~~~~~~~~~~~
- Switch to setuptools-scm for versioning.

Additions
~~~~~~~~~
- Unmark :meth:`~Problem.render` as an abstract method.

v0.4.2
^^^^^^

Additions
~~~~~~~~~
- Make dependency on Matplotlib optional.

Bug fixes
~~~~~~~~~
- Add missing check for defined render modes to :func:`check()`.

v0.4.1
^^^^^^

Bug fixes
~~~~~~~~~
- Expose :func:`check()` argument *headless*.

v0.4.0
^^^^^^

Breaking changes
~~~~~~~~~~~~~~~~
- Mark the package as fully type-annotated.
- Switch to pyproject.toml and setup.cfg based building.
- Rewrite ``check_env()`` as :func:`check()`.

Additions
~~~~~~~~~
- :func:`mpl_utils.iter_matplotlib_figures()
  <cernml.mpl_utils.iter_matplotlib_figures>`.

v0.3
----

v0.3.3
^^^^^^

Bug fixes
~~~~~~~~~
- Set window title in example ``configurable.py``.

v0.3.2
^^^^^^

Additions
~~~~~~~~~
- *help* argument to :meth:`Config.add()`.

v0.3.1
^^^^^^

Breaking changes
~~~~~~~~~~~~~~~~
- Make all submodules private.

Additions
~~~~~~~~~
- :class:`Configurable` interface.

v0.3.0
^^^^^^

Breaking changes
~~~~~~~~~~~~~~~~
- Rename ``Optimizable`` to :class:`SingleOptimizable`.
- Add dependency on Numpy.

Additions
~~~~~~~~~
- :class:`Problem` interface.
- :doc:`Environment registry<api/registration>`.

Bug fixes
~~~~~~~~~
- Check inheritance of :attr:`env.unwrapped<Problem.unwrapped>` in
  :func:`check_env()<check>`.

v0.2
----

v0.2.1
^^^^^^

Bug fixes
~~~~~~~~~
- Fix broken CI tests.

v0.2.0
^^^^^^

Breaking changes
~~~~~~~~~~~~~~~~
- Rename package from ``cernml.abc`` to ``cernml.coi`` (And the
  distribution from ``cernml-abc`` to ``cernml-coi``).
- Rename ``OptimizeMixin`` to
  :class:`Optimizable<SingleOptimizable>`.
- Add :attr:`~Problem.metadata` key :mdkey:`"cern.machine"`.
- Add more restrictions to :func:`env_checker()<check>`.

Additions
~~~~~~~~~
- Virtual inheritance: Any class that implements the required methods of
  our interfaces automatically subclass them, even if they are not direct
  bases.

Bug fixes
~~~~~~~~~
- Make :class:`SeparableOptEnv` subclass :class:`SeparableEnv`.

v0.1
----

v0.1.0
^^^^^^

The dawn of time.
