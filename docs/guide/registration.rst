..
    SPDX-FileCopyrightText: 2020-2024 CERN
    SPDX-FileCopyrightText: 2023-2024 GSI Helmholtzzentrum für Schwerionenforschung
    SPDX-FileNotice: All rights not expressly granted are reserved.

    SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

Making Your Code Findable
=========================

The Common Optimization Interfaces provide a *registry* in which all available
(i.e. locally installed) optimization problems are registered. This registry is
a fork of the :doc:`Gymnasium registry <gym:api/registry>` with an additional
lazy-loading mechanism and minor compatibility adjustments.

The core of the registry API are two functions: `cernml.coi.register()` and
`cernml.coi.make()`. The former registers a class definition as an optimization
problem for later use; the latter instantiates a previously registered class.

Motivation
----------

Most optimization problems are intended to be used as plugins into larger *host
applications*. A host application may be a trivial Python script, but may also
be a larger GUI application that manages multiple independent plugins.

Depending on its complexity, importing a package that provides an optimization
problem may be slow. This is particularly the case if the package has a lot of
dependencies or depends on large libraries. At the same time, any single user
often wants to use only a small fraction of the available plugins at a time.

This means that host applications want to avoid importing any optimization
problems that are not required. At the same time, they *do* have to know that
the problems at least exist, so they can be offered to the user.

Another motivation is to enrich optimization problems with additional metadata
that is required to instantiate them in the first place. This includes e.g.
:doc:`wrappers <gym:api/wrappers>` that should be applied to an
`~gymnasium.Env` automatically.

Finally, the addition of a registry necessitates the introduction of *registry
IDs*. By adding additional semantics to these IDs, e.g. by allowing a suffixed
*version number*, authors may release newer versions of their optimization
problems, which have new behavior, without impacting users that rely on the
particular behavior of an older version.

Registry IDs
------------

Registry IDs follow the same scheme as in :doc:`Gymnasium <gym:api/registry>`:

.. productionlist::
   registry_id: [`namespace` "/"] `name` ["-v" `version`]
   namespace: <words separated by ":" or "-"; regex /[\w:-]+/>
   name: <words separated by ":", "." or "-"; regex /[\w:.-]+/>
   version: <any integer number; regex /\d+/>

The **namespace** is optional and its meaning differs between
`cernml.coi.register()` and `cernml.coi.make()`:

- when calling `~cernml.coi.register()` without a namespace, the problem is
  usually added to the *global namespace*. The global namespace acts like
  a regular but anonymous namespace. Note that if :ref:`guide/registration:Lazy
  Registration via Entry Points` is used to register a problem, the namespace
  is added implicitly.

  .. note::
    This means that if your problem may be registered **both lazily and
    eagerly**, you should provide the namespace for consistency.

- when calling `~cernml.coi.make()`, the correct namespace is always required.
  Calling it without a namespace means to search the global namespace for
  a matching problem.

The **version** number is also optional and may be given both to problems with
and without namespaces. It can be used to release newer versions of a problem
without making the old one unavailable. What happens when the version number is
*not* specified depends, again, on the function that is called:

- when calling `~cernml.coi.register()` without a version number, the problem
  becomes unversioned: Only this version of the problem may exist.
  Any attempt to use this name with a version number will fail.

- when calling `~cernml.coi.make()` without a version number, the highest
  version number available is picked automatically.

Registering a Problem Class
---------------------------

.. Setup for doctest: ignore registry warnings on this page.

    >>> from cernml import coi
    >>> import warnings
    >>> warnings.simplefilter("ignore",
    ...     coi.registration.errors.RegistryWarning)

Problems are registered via the `cernml.coi.register()` function and *only* via
this function. If your package does not contain a `~cernml.coi.register()` call
for your optimization problem, the registry will not know about it.

There are three ways to register a problem, all of which are detailed below:

- :ref:`directly <guide/registration:Direct Registration>` in the same module
  that defines it;
- :ref:`indirectly <guide/registration:Indirect Registration>` in a different
  module than the one that defines it;
- :ref:`lazily <guide/registration:Lazy Registration via Entry Points>` via
  :doc:`entry points <pkg:specifications/entry-points>`.

Direct Registration
^^^^^^^^^^^^^^^^^^^

Simply call `cernml.coi.register()` directly after the class definition of your
optimization problem and pass the class itself as the *entry_point* argument:

    >>> from cernml import coi
    ...
    >>> class BeamSteering(coi.SingleOptimizable):
    ...     def __init__(self, *, render_mode=None, simulation_version="1.0"):
    ...         super().__init__(render_mode)
    ...         self.simver = simulation_version
    ...
    ...     def get_initial_params(self): ...
    ...
    ...     def compute_single_objective(self): ...
    ...
    ...     def __repr__(self):
    ...         name = self.spec.id if self.spec else self.__class__.__name__
    ...         return f"<{name}({self.simver!r})>"
    ...
    >>> coi.register("MyAcc/BeamSteering-v1", entry_point=BeamSteering)

This makes the problem available under the :ref:`registry ID
<guide/registration:Registry IDs>` ``MyAcc/BeamSteering-v1``.
You can register this problem multiple times with different versions, each
being an upgrade of the other, for example:

    >>> coi.register("MyAcc/BeamSteering-v2", entry_point=BeamSteering,
    ...              kwargs={"simulation_version": "1.33"})
    >>> coi.make("MyAcc/BeamSteering-v2")
    <MyAcc/BeamSteering-v2('1.33')>

The advantage of this method is that it is simple and trivial to understand.
The registration code is next to the problem that it registers, so when one
needs an update, it's trivial to update the other.

The disadvantage of this method is that a host application must know your
package and import it in order to be aware of your optimization problem.
In particular, the entire problem logic must be imported. This may be very
expensive if your package has heavy dependencies like e.g. Tensorflow.

Indirect Registration
^^^^^^^^^^^^^^^^^^^^^

The *entry_point* argument to `cernml.coi.register()` may also be a string of
the following format:

.. productionlist::
    register_reference: `module` ":" `attr`
    module: <any Python module, possibly nested>
    attr: <identifier pointing to any callable>

In this case, the optimization problem need not exist at the point when
`~cernml.coi.register()` is called. For example, imagine your optimization
problem is defined in a submodule :file:`my_package/beam_steering.py`:

    >>> # my_package/coi.py
    ...
    >>> from cernml import coi
    ...
    >>> class BeamSteering(coi.SingleOptimizable):
    ...     def __init__(self, *, render_mode=None, simulation_version="1.0"):
    ...         super().__init__(render_mode)
    ...         self.simver = simulation_version
    ...
    ...     def get_initial_params(self): ...
    ...
    ...     def compute_single_objective(self): ...
    ...
    ...     def __repr__(self):
    ...         name = self.spec.id if self.spec else self.__class__.__name__
    ...         return f"<{name}({self.simver!r})>"

Then the parent package, defined in :file:`my_package/__init__.py`, could
contain the following line:

    >>> # my_package/__init__.py
    ...
    >>> from cernml import coi
    ...
    >>> # No `from . import beam_steering`! The BeamSteering class isn't
    >>> # defined yet!
    >>> coi.register(
    ...     "MyAcc/BeamSteering-v3",
    ...     entry_point="my_package.beam_steering:BeamSteering",
    ...     kwargs={"simulation_version": "1.42"},
    ... )

Calling `cernml.coi.make()` would find this indirect reference, automatically
import ``my_package.beam_steering`` and use the ``BeamSteering`` class in it as
the entry point:

.. setup doctest: mock importlib:
    >>> from unittest.mock import patch, Mock
    >>> fake_module = Mock(name="my_package.beam_steering")
    >>> fake_module.BeamSteering = BeamSteering
    >>> patcher = patch("importlib.import_module")
    >>> patcher.__enter__().return_value = fake_module

..

    >>> coi.make("MyAcc/BeamSteering-v3")
    <MyAcc/BeamSteering-v3('1.42')>

.. teardown doctest: remove mock:
    >>> patcher.__exit__(None, None, None)
    False

The advantage of this method is that expensive imports can be avoided: all the
heavy dependencies are only imported in ``my_package.beam_steering``, whereas
``my_package`` itself can very small. It is also still compatible with
:ref:`guide/registration:Direct Registration`\ : if a user imports
``my_package.beam_steering``, they also import ``my_package`` by necessity;
so `~cernml.coi.register()` is going to be called either way.

The disadvantage of this method is that the registration code is further away
from the optimization problem that it registers. This makes it easier to forget
to update it when the code is changed. Also, the host application still has to
know about the package and import it in order to have the problem registered.

Lazy Registration via Entry Points
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The third approach is actually compatible with and an extension of the former
two approaches. By declaring an :doc:`entry point
<pkg:specifications/entry-points>` for your package, you can make your
optimization problem findable by the problem registry even if your package
isn't imported yet at all.

You generally declare entry points in your project manifest file. Which one
this is depends on the specifics of your project, but generally this is either
:file:`setup.py`, :file:`setup.cfg` or :file:`pyproject.toml`. The following
snippet shows how to declare your :ref:`entry point using Setuptools
<setuptools:dynamic discovery of services and plugins>`:

.. tab:: pyproject.toml

   .. code-block:: toml

        [project.entry-points.'cernml.envs']
        MyAcc = 'my_package'
        MyOtherAcc = 'my_package.other_module:some_function'

.. tab:: setup.cfg

   .. code-block:: cfg

        [options.entry_points]
        cernml.envs =
            MyAcc = my_package
            MyOtherAcc = my_package.other_module:some_function

.. tab:: setup.py

   .. code-block:: python

        from setuptools import setup

        setup(
            # ...,
            entry_points = {
                'cernml.envs': [
                    'MyAcc = my_package',
                    'MyOtherAcc = my_package.other_module:some_function',
                ],
            },
        )

The entry point *group* is always :ep:`cernml.envs`. The entry point *name*
must be exactly the *namespace* of your environment ID. The registry always
loads an entire namespace at once. Finally, the entry point *object reference*
(the part after the equals sign ``=``) should be the name of a module plus
optionally the name of a function in that module.

When the user requests an environment from that namespace, the registry will
import the given module and, if a function was given, call that function.
Either the import or the function call is expected to eventually call
`~cernml.coi.register()` for all optimization problems in the requested
namespace.

For example, imagine that this is what :file:`my_package/other_module.py`
looked like:

    >>> # my_package/other_module.py
    ...
    >>> from cernml import coi
    ...
    >>> def some_function():
    ...     # No namespace! It will be inserted by the entry point.
    ...     coi.register(
    ...         "BeamSteering-v1",
    ...         # Indirect registration still works.
    ...         entry_point="my_package.beam_steering:BeamSteering",
    ...         kwargs={"simulation_version": "1.63"},
    ...     )

Attempting to instantiate the problem ``MyOtherAcc/BeamSteering`` finds the
entry point with the name ``MyOtherAcc``, imports the module
``my_package.other_module`` and calls the function ``some_function`` within.
This function then calls `~cernml.coi.register()`, which makes
``MyOtherAcc/BeamSteering-v1`` available. This is then finally instantiated:

.. setup doctest: mock importlib:
    >>> from unittest.mock import patch, Mock
    >>> fake_module = Mock(name="my_package.beam_steering")
    >>> fake_module.BeamSteering = BeamSteering
    >>> patcher = patch("importlib.import_module")
    >>> patcher.__enter__().return_value = fake_module

.. setup doctest: add a fake entry point:
    >>> import sys
    >>> if sys.version_info < (3, 10):
    ...     from importlib_metadata import EntryPoints, EntryPoint
    ... else:
    ...     from importlib.metadata import EntryPoints, EntryPoint
    >>> ep_real = EntryPoint(
    ...     name="MyOtherAcc",
    ...     value="my_package.other_module:some_function",
    ...     group="cernml.envs",
    ... )
    >>> ep = Mock(name="ep", wraps=ep_real)
    >>> vars(ep).update(vars(ep_real))
    >>> ep.load.return_value = some_function
    >>> coi.registry._plugins.entry_points = EntryPoints([ep])
    >>> # Clear the cached property, if necessary:
    >>> vars(coi.registry._plugins).pop("_unloaded_plugins", None)

..

    >>> coi.make("MyOtherAcc/BeamSteering-v1")
    <MyOtherAcc/BeamSteering-v1('1.63')>

.. teardown doctest: remove mock:
    >>> patcher.__exit__(None, None, None)
    False

Problems that are loaded via this mechanism have the namespace of their ID
automatically set to the name of the entry point. If the
`~cernml.coi.register()` call specifies a namespace as well, it must match the
one given via the entry point.

The advantage of this method is that a host application can finally find all
optimization problems that are installed in the application's environment. It
needn't know the problems beforehand and can load them as required. This is the
ideal situation in a large laboratory like CERN, where many problems are
designed in a decentralized fashion and maintainers of an application need to
minimize the effort required to coordinate with these authors.

The disadvantages of this method are obvious: It is much more convoluted than
the other approaches, and packages must be installed in order to have their
entry points be discoverable (though `editable installs`_ alleviate this issue.

.. _editable installs:
   https://pip-python3.readthedocs.io/en/latest/reference/pip_install.html#
   editable-installs

Instantiating a Problem Class
-----------------------------

Similar to :ref:`registration <guide/registration:Registering a Problem
Class>`, there are multiple ways in which a user can instantiate a problem
class:

- :ref:`directly <guide/registration:Direct Instantiation>` via their class
  object;
- :ref:`indirectly <guide/registration:Indirect Instantiation>` via
  `cernml.coi.make()`,
- :ref:`indirectly <guide/registration:Indirect Instantiation with Imports>`
  with an intermediate import.

Direct Instantiation
^^^^^^^^^^^^^^^^^^^^

Any subclass of `cernml.coi.Problem` can be instantiated directly like any
normal Python type:

    >>> BeamSteering(render_mode=None, simulation_version="1.23")
    <BeamSteering('1.23')>

This is the most straightforward way, but obviously does not come with the
features provided by `~cernml.coi.make()`. Also, the module that defines the
problem class must have been imported already for this to work. Thus, this
method is best suited for quick debugging sessions and one-off scripts.

Indirect Instantiation
^^^^^^^^^^^^^^^^^^^^^^

The recommended way to instantiate optimization problems is with the function
`cernml.coi.make()`. As shown in examples further above, it takes
a :ref:`registry ID <guide/registration:Registry IDs>` and any number of
further configuration options. The problem is looked up by the ID it was
:ref:`registered <guide/registration:Registering a Problem Class>` under and
any arguments not used by `~cernml.coi.make()` are passed on to its
:meth:`~object.__init__()` method:

.. setup doctest: mock importlib:
    >>> from unittest.mock import patch, Mock
    >>> fake_module = Mock(name="my_package.beam_steering")
    >>> fake_module.BeamSteering = BeamSteering
    >>> patcher = patch("importlib.import_module")
    >>> patcher.__enter__().return_value = fake_module

..

    >>> coi.make("MyAcc/BeamSteering-v2", simulation_version="2.1")
    <MyAcc/BeamSteering-v2('2.1')>

If the problem has a :ref:`versioned ID <guide/registration:Registry IDs>`, you
can also leave off the version number and `~cernml.coi.make()` will pick the
highest available version:

    >>> coi.make("MyAcc/BeamSteering")
    <MyAcc/BeamSteering-v3('1.42')>

Whether or not the module that defines the problem has to have been imported
depends on how precisely the problem was registered. See
:ref:`guide/registration:Registering a Problem Class` for the details.

If you are loading an `~gymnasium.Env` instead of
a `~cernml.coi.SingleOptimizable`, one further advantage of using
`~cernml.coi.make()` is that it applies several convenient wrappers to your
environment upon creation. (Again, this behavior is copied directly from
:func:`gymnasium.make()`):

    >>> from gymnasium import Env
    >>> from gymnasium.spaces import Box
    ...
    >>> class InjectionEnv(Env):
    ...     action_space = Box(-1.0, 1.0, (2,))
    ...     observation_space = Box(-1.0, 1.0, (5,))
    ...
    ...     def __init__(self, render_mode=None):
    ...         super().__init__()
    ...         self.render_mode = render_mode
    ...
    ...     def __repr__(self):
    ...         return str(self)
    ...
    >>> coi.register("MyAcc/InjectionEnv-v1", entry_point=InjectionEnv)
    >>> coi.make("MyAcc/InjectionEnv-v1")
    <OrderEnforcing<PassiveEnvChecker<InjectionEnv<MyAcc/InjectionEnv-v1>>>>

Which of these wrappers get applied (and which don't) depends on parameters
that are interpreted by `~cernml.coi.make()` instead of being passed on:

    >>> coi.make(
    ...     "MyAcc/InjectionEnv-v1",
    ...     disable_env_checker=True,
    ...     order_enforce=False,
    ... )
    <InjectionEnv<MyAcc/InjectionEnv-v1>>

.. teardown doctest: remove mock:
    >>> patcher.__exit__(None, None, None)
    False

Indirect Instantiation with Imports
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The `cernml.coi.make()` has one final feature that is similar to
:ref:`guide/registration:Indirect Registration`. If you pass a string like
:samp:`"{module}:{registry_id}"` to it, the given :samp:`{module}` will be
imported (and any calls to `~cernml.coi.register()` executed) before the
problem with ID :samp:`{registry_id}` is looked up.

It is useful to keep in mind that any registration that happens upon import
of ``module`` might itself be indirect and so may incur further imports before
the problem's *entry_point* can be called.
