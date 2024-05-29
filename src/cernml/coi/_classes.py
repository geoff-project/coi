# SPDX-FileCopyrightText: 2020-2024 CERN
# SPDX-FileCopyrightText: 2023-2024 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

"""Provide `Problem`, the most fundamental API of this package."""

from __future__ import annotations

import typing as t
import warnings
from abc import ABCMeta, abstractmethod
from types import MappingProxyType

import numpy as np
from gymnasium import Env
from gymnasium.envs.registration import EnvSpec as GymEnvSpec
from gymnasium.spaces import Space
from gymnasium.utils import seeding

from . import protocols
from ._machine import Machine
from .protocols import Constraint, ParamType
from .registration import errors

if t.TYPE_CHECKING:
    from typing_extensions import Self

__all__ = (
    "Constraint",
    "Env",
    "FunctionOptimizable",
    "HasNpRandom",
    "ParamType",
    "Problem",
    "SingleOptimizable",
)


class HasNpRandom:
    """Mixin that replicates the `gymnasium.Env.np_random` property."""

    _np_random: np.random.Generator | None = None

    @property
    def np_random(self) -> np.random.Generator:
        """Returns the environment's internal :attr:`_np_random`.

        if `_np_random` is not set yet, this will initialize it with
        a random seed.

        Returns:
            Instances of `np.random.Generator`
        """
        if self._np_random is None:
            self._np_random, _ = seeding.np_random()
        return self._np_random

    @np_random.setter
    def np_random(self, value: np.random.Generator) -> None:
        self._np_random = value


@protocols.Problem.register
class Problem(HasNpRandom, metaclass=ABCMeta):
    """ABC that implements the `Problem` protocol.

    Subclassing this :term:`abstract base class` instead of `Problem`
    directly comes with a few advantages for convenience:

    - an `~object.__init__()` method that ensures that the `render_mode`
      attribute is set correctly;
    - :term:`context manager` methods that ensure that `close()` is
      called when using the problem in a :keyword:`with` statement;
    - the attribute `~HasNpRandom.np_random` as an exclusive and
      seedable `~numpy.random` number generator.

    To check whether an object satisfies the `Problem` protocol, use the
    dedicated function `is_problem()`. Alternatively, you may also call
    ``isinstance(obj.unwrapped, Problem)``. Do not use this class for
    such checks!

    Equivalent base classes also exist for the other interfaces.

    See Also:
        `BaseFunctionOptimizable`, `BaseSingleOptimizable`, `Env`
    """

    # pylint: disable = missing-function-docstring
    metadata: dict[str, t.Any] = t.cast(
        dict[str, t.Any],
        MappingProxyType(
            {
                "render_modes": [],
                "cern.machine": Machine.NO_MACHINE,
                "cern.japc": False,
                "cern.cancellable": False,
            }
        ),
    )
    render_mode: str | None = None

    # HACK: We say this is a Gym EnvSpec, but in fact it will almost
    # always be a COI EnvSpec. This is so that `OptEnv` can be
    # a subclass of both `gym.Env` and `coi.SingleOptimizable` without
    # conflicts.
    #
    # The two spec classes are nearly identical and Gym's specs are
    # a virtual subclass of the COI's. If it is important to you to get
    # the typing of this attribute right, use `coi.protocols.Problem`
    # as annotation instead of this class.
    spec: GymEnvSpec | None = None

    def __init__(self, render_mode: str | None = None) -> None:
        super().__init__()
        modes: t.Collection[str] | None = self.metadata.get("render.modes", None)
        if modes is not None:
            warnings.warn(
                errors.GymDeprecationWarning(
                    "metadata key 'render.modes'", "'render_modes'"
                ),
                stacklevel=2,
            )
        if render_mode is not None:
            modes = t.cast(
                t.Collection[str], self.metadata.get("render_modes", modes or ())
            )
            if render_mode not in modes:
                raise ValueError(
                    f"invalid render mode: expected one of {modes}, "
                    f"got {render_mode!r}"
                )
        self.render_mode = render_mode

    def __enter__(self) -> "Self":
        return self

    # pylint: disable = useless-return
    def __exit__(self, *args: object) -> bool | None:
        self.close()
        return None

    # pylint: enable = useless-return

    def close(self) -> None:
        return None

    def render(self) -> t.Any:
        assert True
        raise NotImplementedError

    @property
    def unwrapped(self) -> protocols.Problem:
        return self

    def get_wrapper_attr(self, name: str) -> t.Any:
        return getattr(self, name)

    @classmethod
    def __subclasshook__(cls, other: type) -> bool:
        # ABCMeta calls `cls.__subclasshook__(protocol)` to guard
        # against cyclic inheritance. This happens before `cls`
        # has been bound to its name in the module. We have to catch
        # this here or `is not cls` will raise `NameError`.
        if other is protocols.Problem or cls is not Problem:
            return NotImplemented
        # Run `issubclass(other, protocol)` but skip
        # `ABCMeta.__subclasscheck__()`, since that would lead to
        # infinite recursion.
        return protocols.Problem.__subclasshook__(other)


@protocols.SingleOptimizable.register
class SingleOptimizable(Problem, t.Generic[ParamType]):
    """ABC that implements the `SingleOptimizable` protocol.

    Subclassing this :term:`abstract base class`  instead of
    `SingleOptimizable` directly comes with a few advantages for
    convenience:

    - an `~object.__init__()` method that ensures that the `render_mode`
      attribute is set correctly;
    - :term:`context manager` methods that ensure that `close()` is
      called when using the problem in a :keyword:`with` statement;
    - the attribute `~HasNpRandom.np_random` as an exclusive and
      seedable `~numpy.random` number generator;
    - a `SingleOptimizable.compute_single_objective()` method that
      automatically calls `~Problem.render()` if in render mode
      ``human``.

    To check whether an object satisfies the `SingleOptimizable`
    protocol, use the dedicated function `is_single_optimizable()`.
    Alternatively, you may also call ``isinstance(obj.unwrapped,
    SingleOptimizable)``. Do not use this class for such checks!

    Equivalent base classes also exist for the other interfaces.

    See Also:
        `BaseFunctionOptimizable`, `BaseProblem`, `Env`
    """

    optimization_space: Space[ParamType]
    objective_range: tuple[float, float] = (-float("inf"), float("inf"))
    constraints: t.Sequence[Constraint] = []

    objective_name: str = ""
    param_names: t.Sequence[str] = []
    constraint_names: t.Sequence[str] = []

    @abstractmethod
    def get_initial_params(
        self, *, seed: int | None = None, options: dict[str, t.Any] | None = None
    ) -> ParamType:
        """See `SingleOptimizable.get_initial_params()`."""  # noqa: D402
        if seed is not None:
            self._np_random, _ = seeding.np_random(seed)
        return  # type: ignore[return-value]

    @abstractmethod
    def compute_single_objective(self, params: ParamType) -> t.SupportsFloat:
        """See `SingleOptimizable.compute_single_objective()`."""  # noqa: D402
        raise NotImplementedError

    @classmethod
    def __subclasshook__(cls, other: type) -> bool:
        # ABCMeta calls `cls.__subclasshook__(protocol)` to guard
        # against cyclic inheritance. This happens before `cls`
        # has been bound to its name in the module. We have to catch
        # this here or `is not cls` will raise `NameError`.
        if other is protocols.SingleOptimizable or cls is not SingleOptimizable:
            return NotImplemented
        # Run `issubclass(other, protocol)` but skip
        # `ABCMeta.__subclasscheck__()`, since that would lead to
        # infinite recursion.
        return protocols.SingleOptimizable.__subclasshook__(other)


@protocols.FunctionOptimizable.register
class FunctionOptimizable(Problem, t.Generic[ParamType]):
    """ABC that implements the `FunctionOptimizable` protocol.

    Subclassing this :term:`abstract base class`  instead of
    `FunctionOptimizable` directly comes with a few advantages for
    convenience:

    - an `~object.__init__()` method that ensures that the `render_mode`
      attribute is set correctly;
    - :term:`context manager` methods that ensure that `close()` is
      called when using the problem in a :keyword:`with` statement;
    - the attribute `~HasNpRandom.np_random` as an exclusive and
      seedable `~numpy.random` number generator.
    - a `FunctionOptimizable.compute_single_objective()` method that
      automatically calls `~Problem.render()` if in render mode
      ``human``.

    To check whether an object satisfies the `FunctionOptimizable`
    protocol, use the dedicated function `is_function_optimizable()`.
    Alternatively, you may also call ``isinstance(obj.unwrapped,
    FunctionOptimizable)``. Do not use this class for such checks!

    Equivalent base classes also exist for the other interfaces.

    See Also:
        `BaseSingleOptimizable`, `BaseProblem`, `Env`
    """

    objective_range: tuple[float, float] = (-float("inf"), float("inf"))
    constraints: t.Sequence[Constraint] = []

    @abstractmethod
    def get_optimization_space(self, cycle_time: float) -> Space[ParamType]:
        """See `FunctionOptimizable.get_optimization_space()`."""  # noqa: D402
        raise NotImplementedError

    @abstractmethod
    def get_initial_params(
        self,
        cycle_time: float,
        *,
        seed: int | None = None,
        options: dict[str, t.Any] | None = None,
    ) -> ParamType:
        """See `FunctionOptimizable.get_initial_params()`."""  # noqa: D402
        if seed is not None:
            self._np_random, _ = seeding.np_random(seed)
        return  # type: ignore[return-value]

    @abstractmethod
    def compute_function_objective(self, cycle_time: float, params: ParamType) -> float:
        """See `FunctionOptimizable.compute_function_objective`."""
        raise NotImplementedError

    def get_objective_function_name(self) -> str | None:
        """See `FunctionOptimizable.get_objective_function_name`."""
        return None

    def get_param_function_names(self) -> list[str]:
        """See `FunctionOptimizable.get_param_function_names`."""
        return []

    def override_skeleton_points(self) -> list[float] | None:
        """See `FunctionOptimizable.override_skeleton_points`."""
        return None

    @classmethod
    def __subclasshook__(cls, other: type) -> bool:
        # ABCMeta calls `cls.__subclasshook__(protocol)` to guard
        # against cyclic inheritance. This happens before `cls`
        # has been bound to its name in the module. We have to catch
        # this here or `is not cls` will raise `NameError`.
        if other is protocols.FunctionOptimizable or cls is not FunctionOptimizable:
            return NotImplemented
        # Run `issubclass(other, protocol)` but skip
        # `ABCMeta.__subclasscheck__()`, since that would lead to
        # infinite recursion.
        return protocols.FunctionOptimizable.__subclasshook__(other)
