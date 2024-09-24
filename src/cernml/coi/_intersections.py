# SPDX-FileCopyrightText: 2020 - 2024 CERN
# SPDX-FileCopyrightText: 2023 - 2024 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

"""These protocols are intersections of various types of problems.

An `intersection protocol`_ indicates that a type implements all
protocols that are part of the intersection. Taking for example
`OptEnv`, an intersection of `~.coi.SingleOptimizable` and `~.coi.Env`,
you can shorten your line of base classes:

    >>> from gymnasium.spaces import Box
    >>> from gymnasium import Env
    >>> from cernml import coi
    ...
    >>> class Both(coi.OptEnv):
    ...     def __init__(self, render_mode=None):
    ...         super().__init__(render_mode)
    ...         self.optimization_space = Box(-1, 1)
    ...         self.observation_space = Box(-1, 1)
    ...         self.action_space = Box(-1, 1)
    ...
    ...     def get_initial_params(self): ...
    ...
    ...     def compute_single_objective(self, params): ...
    ...
    >>> env = Both()
    >>> isinstance(env, coi.SingleOptimizable)
    True
    >>> isinstance(env, Env)
    True
    >>> isinstance(env, coi.OptEnv)
    True

Vice versa, you can use intersection protocols to test if a class
implements both protocols, even if it doesn't directly subclass the
intersection protocol:

    >>> class Indirect(Env, coi.SingleOptimizable):
    ...     def __init__(self, render_mode=None):
    ...         super().__init__(render_mode)
    ...         self.optimization_space = Box(-1, 1)
    ...         self.observation_space = Box(-1, 1)
    ...         self.action_space = Box(-1, 1)
    ...
    ...     def get_initial_params(self): ...
    ...
    ...     def compute_single_objective(self, params): ...
    ...
    >>> env = Indirect()
    >>> isinstance(env, coi.SingleOptimizable)
    True
    >>> isinstance(env, Env)
    True
    >>> isinstance(env, coi.OptEnv)
    True

The intersection protocols of this package come with a few limitations
given by the implementation:

- Implementors must be real subclasses of one of the environment
  base classes (`~gymnasium.Env` or one of the :doc:`sep_goal_env`), be
  it direct or indirect. :term:`Virtual subclasses <abstract base
  class>` are not recognized.

  This restriction is given by `~gymnasium.Env` not actually being
  a `Protocol`; accordingly, it does not apply to
  `~.coi.SingleOptimizable`.

- Static type checkers like MyPy_ generally don't recognize the
  intersections as true protocols, even though they behave as such at
  runtime. Again, this is a limitation of `~gymnasium.Env` not actually
  being a `Protocol`.

- Implementor *classes* that *don't subclass* an intersection protocol
  must provide all three spaces [#spaces]_ as :term:`attributes
  <attribute>` or `properties <property>` at class scope to be
  recognized as subclasses. Type annotations are not sufficient.

  This restriction is given by the fact that for protocols,
  :func:`issubclass()` only checks the type hints of a subclass if the
  subclass is itself a protocol. If the subclass is concrete (i.e. not
  a protocol) and also doesn't have a protocol among its bases, there is
  no way for Python to verify the implementation.

- Implementor *instances*, on the other hand, merely need to *define*
  the three spaces [#spaces]_. This may happen e.g. within
  :meth:`~object.__init__()`. This may lead to the situation that
  a class ``MyEnv`` is not a *subclass* of `OptEnv`, but ``MyEnv()`` is
  an *instance* of it. This is simply given by the dynamic nature of
  Python.

.. [#spaces]
    These spaces are `~.coi.SingleOptimizable.optimization_space`,
    `~gymnasium.Env.observation_space` and
    `~gymnasium.Env.action_space`.

.. _intersection protocol:
    https://typing.readthedocs.io/en/latest/spec/protocol.html
    #unions-and-intersections-of-protocols

.. _MyPy: https://mypy.readthedocs.io/
"""

from __future__ import annotations

import typing as t
from abc import abstractmethod

from gymnasium.core import ActType, Env, ObsType
from typing_extensions import override

from ._classes import ParamType, SingleOptimizable
from ._goalenv import GoalEnv, GoalType
from ._machinery import (
    AttrCheckProtocolMeta,
    get_static_mro,
    non_callable_proto_members,
    proto_hook,
)
from ._sepenv import SeparableEnv, SeparableGoalEnv

__all__ = (
    "OptEnv",
    "OptGoalEnv",
    "SeparableOptEnv",
    "SeparableOptGoalEnv",
)


class OptEnv(
    Env[ObsType, ActType], SingleOptimizable[ParamType], metaclass=AttrCheckProtocolMeta
):
    """An intersection of `Env` and `SingleOptimizable`.

    Any class that inherits from both also inherits from this class.
    """

    # Lie about being a protocol. We can't subclass Protocol directly
    # because `Env` is not a protocol class. This also prevents us from
    # using `@runtime_checkable`, so we lie about that as well.
    _is_protocol = True
    _is_runtime_protocol = True

    @classmethod
    def __subclasshook__(cls, other: type) -> bool:
        # Our environment base class must be not only implemented by
        # protocol, it must also be in our MRO. Otherwise, SeparableEnv
        # and SeparableGoalEnv would overlap. Preventing this overlap is
        # one of our goals.
        if Env not in get_static_mro(other):
            return False
        return proto_hook.__get__(None, cls)(other)


class SeparableOptEnv(
    SeparableEnv[ObsType, ActType],
    SingleOptimizable[ParamType],
    metaclass=AttrCheckProtocolMeta,
):
    """An intersection of `SeparableEnv` and `SingleOptimizable`.

    Any class that inherits from both also inherits from this class.
    """

    # Lie about this being a runtime protocol so that `attrs_match()`
    # is run.
    _is_protocol = True
    _is_runtime_protocol = True

    @classmethod
    def __subclasshook__(cls, other: type) -> bool:
        # Our environment base class must be not only implemented by
        # protocol, it must also be in our MRO. Otherwise, SeparableEnv
        # and SeparableGoalEnv would overlap. Preventing this overlap is
        # one of our goals.
        if SeparableEnv not in get_static_mro(other):
            return False
        return proto_hook.__get__(None, cls)(other)


class OptGoalEnv(
    GoalEnv,
    SingleOptimizable[ParamType],
    t.Generic[ObsType, GoalType, ActType, ParamType],
    metaclass=AttrCheckProtocolMeta,
):
    """An intersection of `GoalEnv` and `SingleOptimizable`.

    Any class that inherits from both also inherits from this class.
    """

    # Lie about this being a runtime protocol so that `attrs_match()`
    # is run.
    _is_protocol = True
    _is_runtime_protocol = True

    @classmethod
    def __subclasshook__(cls, other: type) -> bool:
        # Our environment base class must be not only implemented by
        # protocol, it must also be in our MRO. Otherwise, SeparableEnv
        # and SeparableGoalEnv would overlap. Preventing this overlap is
        # one of our goals.
        if GoalEnv not in get_static_mro(other):
            return False
        return proto_hook.__get__(None, cls)(other)

    # Repeat GoalEnv methods here so that they get type annotations even
    # if `gymnasium_robotics.GoalEnv` doesn't have any.
    @override
    @abstractmethod
    def compute_reward(
        self, achieved_goal: GoalType, desired_goal: GoalType, info: dict[str, t.Any]
    ) -> t.SupportsFloat:
        raise NotImplementedError

    @override
    @abstractmethod
    def compute_terminated(
        self, achieved_goal: GoalType, desired_goal: GoalType, info: dict[str, t.Any]
    ) -> bool:
        raise NotImplementedError

    @override
    @abstractmethod
    def compute_truncated(
        self, achieved_goal: GoalType, desired_goal: GoalType, info: dict[str, t.Any]
    ) -> bool:
        raise NotImplementedError


class SeparableOptGoalEnv(
    SeparableGoalEnv[ObsType, GoalType, ActType],
    SingleOptimizable[ParamType],
    metaclass=AttrCheckProtocolMeta,
):
    """An intersection of `SeparableGoalEnv` and `SingleOptimizable`.

    Any class that inherits from both also inherits from this class.
    """

    # Lie about this being a runtime protocol so that `attrs_match()`
    # is run.
    _is_protocol = True
    _is_runtime_protocol = True

    @classmethod
    def __subclasshook__(cls, other: type) -> bool:
        # Our environment base class must be not only implemented by
        # protocol, it must also be in our MRO. Otherwise, SeparableEnv
        # and SeparableGoalEnv would overlap. Preventing this overlap is
        # one of our goals.
        if SeparableGoalEnv not in get_static_mro(other):
            return False
        return proto_hook.__get__(None, cls)(other)


non_callable_proto_members(OptEnv)
non_callable_proto_members(SeparableOptEnv)
non_callable_proto_members(OptGoalEnv)
non_callable_proto_members(SeparableOptGoalEnv)
