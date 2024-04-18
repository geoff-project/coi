..
    SPDX-FileCopyrightText: 2020-2024 CERN
    SPDX-FileCopyrightText: 2023-2024 GSI Helmholtzzentrum für Schwerionenforschung
    SPDX-FileNotice: All rights not expressly granted are reserved.

    SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

The Problem Registry
====================

.. seealso::

    :doc:`/guide/registration`
        User guide page on the topic.

.. automodule:: cernml.coi.registration
    :no-members:

.. currentmodule:: cernml.coi

.. autofunction:: register

.. autofunction:: make

.. autofunction:: make_vec

.. autofunction:: spec

.. autofunction:: pprint_registry


.. function:: cernml.coi.register_envs(env_module: ~types.ModuleType)

    A no-op function such that it can appear to IDEs that a module is used.

    This has been re-exported from Gymnasium.

.. data:: registry
    :type: EnvRegistry
    :value: EnvRegistry(ep_group="cernml.envs")

    The global variable that contains all registered environments. If possible,
    you should call the global functions instead of this variable's methods.

Advanced Registration Features
------------------------------

.. currentmodule:: cernml.coi.registration

.. autoclass:: EnvRegistry

.. autoclass:: EnvSpec

.. autoclass:: MinimalEnvSpec

.. autofunction:: downcast_spec

.. autoclass:: cernml.coi.registration._sentinel.Sentinel

.. autodata:: cernml.coi.registration._sentinel.MISSING
    :no-value:

.. function:: make_vec(id: str | EnvSpec, num_envs: int = 1, vectorization_mode: str = 'async', vector_kwargs: dict[str, typing.Any] | None = None, wrappers: typing.Sequence[typing.Callable[[~cernml.coi.Env], Wrapper]] | None = None, **kwargs: typing.Any) -> VectorEnv
    :module: gymnasium

    Create a vector environment according to the given ID.

    .. note::

        This feature is experimental, and is likely to change in future
        releases.

.. function:: gymnasium.envs.registration.EnvCreator(**kwargs: typing.Any) -> ~gymnasium.Env
    :single-line-parameter-list:

    The call signature of entry points accepted by `~cernml.coi.register()`.
    This is used merely for type annotations.

.. function:: gymnasium.envs.registration.VectorEnvCreator(**kwargs: typing.Any) -> ~gymnasium.experimental.vector.VectorEnv
    :single-line-parameter-list:

    The call signature of vector entry points accepted by
    `~cernml.coi.register()`. This is used merely for type annotations.

.. autoclass:: gymnasium.envs.registration.WrapperSpec

Exceptions Raised by the Registry
---------------------------------

.. automodule:: cernml.coi.registration.errors
