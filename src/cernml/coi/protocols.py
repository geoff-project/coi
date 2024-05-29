# SPDX-FileCopyrightText: 2020-2024 CERN
# SPDX-FileCopyrightText: 2023-2024 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

"""The protocols that underlie the :doc:`classes`.

The core classes contain several convenience features that are not
relevant to the API defined by this package. For example, a class need
not have an attribute `~.coi.Problem.np_random` in order to satistfy the
`SingleOptimizable` interface. This means that the core classes
themselves are not suited to check whether an object satisfies one of
our interfaces.

Instead, this definition is done by the protocols defined in this
module. They are derived from a subclass of `typing.Protocol` and are
all `~typing.runtime_checkable`. This subclass is described in
:doc:`machinery`, but it extends the checks performed by standard
runtime-checkable protocols.

This page lists the pure protocols and their properties. Their
individual documentation is kept concise. For the full details, refer to
the :doc:`classes`.
"""

from __future__ import annotations

import typing as t
from abc import abstractmethod
from types import MappingProxyType

import numpy as np
from gymnasium import Env
from gymnasium.spaces import Space

from ._machine import Machine
from ._machinery import AttrCheckProtocol
from .registration import MinimalEnvSpec

if t.TYPE_CHECKING:
    import scipy.optimize  # noqa: F401, RUF100

__all__ = (
    "Constraint",
    "Env",
    "FunctionOptimizable",
    "HasNpRandom",
    "ParamType",
    "Problem",
    "SingleOptimizable",
    "Space",
)


# See note in AttrCheckProtocol on why we also subclass Protocol itself.
@t.runtime_checkable
class HasNpRandom(AttrCheckProtocol, t.Protocol):
    """Pure protocol version of `.coi.HasNpRandom`."""

    np_random: np.random.Generator
    """A random-number generator (RNG) for exclusive use by the class
    that owns it. It may be implemented as a `property` to support lazy
    initialization. If implemented as a property, it must be settable in
    order to support reseeding.

    Start-up functions like `SingleOptimizable.get_initial_params()` or
    :func:`Env.step() <gymnasium.Env.step()>` should make sure to reseed
    it if required.
    """


@t.runtime_checkable
class Problem(AttrCheckProtocol, t.Protocol):
    """Pure protocol version of `.coi.Problem`.

    As with the full class, this merely presents the commonalities
    between very different protocols such as `Env` and
    `SingleOptimizable`. On its own, it isn't terribly interesting.
    """

    # Subclasses should make `metadata` just a regular dict. This is
    # a mapping proxy here to prevent accidental mutation through
    # inheritance.
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
    """Capabilities and behavior of this optimization problem.

    Ideally, this is an immutable, class-scope attribute that does not
    get replaced after the problem has been instantiated. Unfortunately,
    there are various exceptions to this:

    - Wrappers often cannot define their metadata at the class scope.
      For them, metadata only makes sense at the instance level.
    - Certain metadata items (e.g. ``"render_fps"``) may be determined
      at instantiation time by certain optimization problems. In this
      case, metadata often exists both at the class and instance scope,
      but they disagree on some items.

    So far, no optimization problem has been observed that modifies an
    existing metadata mapping. If *any* updates are necessary, it is
    considered best practice to :func:`~copy.deepcopy()` the existing
    instance, modify the copy, and then replace the original.

    The protocol defines *metadata* as a `dict` for compatibility
    reasons, but actually binds it to a `types.MappingProxyType` object.
    This is done as a safety measure, to prevent accidental overwrites
    of globally visible data.
    """

    @property
    def render_mode(self) -> str | None:
        """The render mode as determined during initialization.

        This attribute is expected to be set inside ``__init__()`` and
        then not changed again.

        This is marked as read-only for compatibility with
        `gymnasium.Wrapper`, where it is not writable. However,
        implementors of this protocol are expected to replace this with
        a either a regular attribute or a writable property.

        The default implementation of this property simply looks up
        *render_mode* in the instance dict. You can set this value with
        a line like the following:

        .. code-block:: python

            vars(self)["render_mode"] = "human"
        """
        return vars(self).get("render_mode")

    @property
    def spec(self) -> MinimalEnvSpec | None:
        """Pre-instantiation metadata on how the problem was initialized.

        This property is usually set by `~cernml.coi.make()`. You
        generally should not modify it yourself. Wrappers should
        :func:`~copy.deepcopy()` the spec of the wrapped environment and
        make their modifications on the copy.

        The type of this property is marked as a minimal compromise
        between `cernml.coi.registration.EnvSpec` and
        `gymnasium.envs.registration.EnvSpec`. This is to convince MyPy
        that `Env` implements this protocol.

        This property is marked as read-only so that MyPy treats it as
        covariant_. All subclasses replace it with a regular attribute,
        however. To avoid any errors, `cernml.coi.make()` circumvents
        the property and sets the spec directly in the instance dict:

        .. code-block:: python

            vars(problem)["spec"] = the_spec

        .. _covariant:
            https://peps.python.org/pep-0484/#covariance-and-contravariance
        """
        return vars(self).get("spec")

    def close(self) -> None:
        """Perform any necessary cleanup.

        Note that the :term:`context manager` protocol is not required
        by this protocol. However, because every problem has a close
        method, you can always use :func:`contextlib.closing()` to
        emulate it, even if a concrete problem is not a context manager
        itself.
        """
        return None  # noqa: RET501

    @property
    def unwrapped(self) -> "Problem":
        """Return the core problem.

        This exists to support the `~gymnasium.Wrapper` design pattern.
        Note that the type of this property is ``Problem``, whereas that
        of `gymnasium.Env.unwrapped` is ``Env``.
        """
        return self

    def render(self) -> t.Any:
        """Render the environment.

        The default implementation simply raises `NotImplementedError`.
        Implementors are encouraged to call :samp:`super().render()` in
        case of an unknown render mode in order to fail in
        a conventionally understood manner.

        Note that even though this method raises `NotImplementedError`,
        it is *not* an abstract method. It need not be implemented by
        implementors who don't support any rendering.
        """
        # pylint: disable = unused-argument
        # Make PyLint realize that this method is not abstract. We do
        # allow people to not override this method in their subclass.
        # However, PyLint thinks that any method that raises
        # NotImplementedError should be overridden.
        assert True
        raise NotImplementedError

    def get_wrapper_attr(self, name: str) -> t.Any:
        """Gets the attribute *name* from the environment.

        This exists to support the `~gymnasium.Wrapper` design pattern.
        """
        return getattr(self, name)


Constraint = t.Union[
    "scipy.optimize.LinearConstraint", "scipy.optimize.NonlinearConstraint"
]

ParamType = t.TypeVar("ParamType")  # pylint: disable = invalid-name


@t.runtime_checkable
class SingleOptimizable(Problem, t.Protocol[ParamType]):
    """Pure protocol version of `.coi.SingleOptimizable`.

    Minimal implementors who subclass this protocol directly must at least:

    1. define `optimization_space`;
    2. implement `get_initial_params()`;
    3. implement `compute_single_objective()`,

    to qualify as a subclass.
    """

    render_mode: str | None = None
    """The render mode as determined during initialization. Unlike for
    `Protocol`, this is a regular attribute. Nonetheless, this attribute
    is expected to be set inside ``__init__()`` and then not changed
    again."""

    optimization_space: Space[ParamType]
    """The phase space of parameters returned by `get_initial_params()`
    and accepted by `compute_single_objective()`. This attribute is
    merely annotated, not defaulted. Implementors *must* provide it
    themselves."""

    objective_range: tuple[float, float] = (-float("inf"), float("inf"))
    """The range in which the return value of
    `compute_single_objective()` will lie."""

    constraints: t.Sequence[Constraint] = ()
    """The constraints that apply to this optimization problem. Not all
    optimization algorithms are able to handle constraints and they may
    be violated by an algorithm."""

    objective_name: str = ""
    """A custom name for the objective function."""

    param_names: t.Sequence[str] = ()
    """Custom names for each of the parameters of the problem. If not
    empty, this should have exactly as many items as the
    `optimization_space`."""

    constraint_names: t.Sequence[str] = ()
    """Custom names for each of the `constraints` of the problem. If not
    empty, this should have exactly as many items as the
    `constraints`."""

    @abstractmethod
    def get_initial_params(
        self, *, seed: int | None = None, options: dict[str, t.Any] | None = None
    ) -> ParamType:
        """Return an initial set of parameters for optimization.

        Because the protocol version of this method cannot assume that
        the optimization problem has an RNG, it does not come with the
        same default implementation as
        `.coi.SingleOptimizable.get_initial_params()`.

        Args:
            seed: Optional. If passed and the problem contains
                a random-number generator (RNG), the RNG is re-seeded
                with this value.
            options: A mapping of custom options that a problem may
                interpret as desired.

        Returns:
            A set of parameters suitable to be passed to
            `compute_single_objective()`. This should be within the
            bounds of `optimization_space`. If it isn't, a host
            application may still choose to pass this value to
            `compute_single_objective()` in order to reset the problem's
            internal state.
        """

    @abstractmethod
    def compute_single_objective(self, params: ParamType) -> t.SupportsFloat:
        """Perform an optimization step.

        Args:
            params: The parameters for which the loss shall be
                calculated. This must have the same structure, as
                `optimization_space`. It should be within the bounds of
                the space, but if this is exactly the value returned by
                `get_initial_params()`, it might exceed them.

        Returns:
            The objective associated with these parameters, also known
            as loss or cost. Numerical optimizers may want to minimize
            this value.
        """


@t.runtime_checkable
class FunctionOptimizable(Problem, t.Protocol[ParamType]):
    """Pure protocol version of `.coi.FunctionOptimizable`.

    Minimal implementors who subclass this protocol directly must at
    least implement the three abstract methods –
    `get_optimization_space()`, `get_initial_params()`, and
    `compute_function_objective()` – to qualify as a subclass.
    """

    render_mode: str | None = None
    """The render mode as determined during initialization. Unlike for
    `Protocol`, this is a regular attribute. Nonetheless, this attribute
    is expected to be set inside ``__init__()`` and then not changed
    again."""

    objective_range: tuple[float, float] = (-np.inf, np.inf)
    """The range in which the return value of
    `compute_function_objective()` will lie."""

    constraints: t.Sequence[Constraint] = []
    """Custom names for each of the `constraints` of the problem. If not
    empty, this should have exactly as many items as the
    `constraints`."""

    @abstractmethod
    def get_optimization_space(self, cycle_time: float) -> Space[ParamType]:
        """Return the optimization space for a given point in time.

        This should return the phase space of the parameters, ideally
        a `~gymnasium.spaces.Box`. While the bounds of the returned
        space may depend on *cycle_time*, its shape should not.

        The default implementation raises `NotImplementedError`.
        """
        raise NotImplementedError

    @abstractmethod
    def get_initial_params(
        self,
        cycle_time: float,
        *,
        seed: int | None = None,
        options: dict[str, t.Any] | None = None,
    ) -> ParamType:
        """Return an initial set of parameters for optimization.

        Because the protocol version of this method cannot assume that
        the optimization problem has an RNG, it does not come with the
        same default implementation as
        `.coi.FunctionOptimizable.get_initial_params()`.

        Args:
            cycle_time: The point in time at which the objective is
                being optimized. Typically measured in integer
                milliseconds from the start of a cycle in the machine.
            seed: Optional. If passed and the problem contains
                a random-number generator (RNG), the RNG is re-seeded
                with this value.
            options: A mapping of custom options that a problem may
                interpret as desired.

        Returns:
            A set of parameters suitable to be passed to
            `compute_function_objective()`. This should be within the
            bounds of the space returned by `get_optimization_space()`.
            If it isn't, a host application may still choose to pass
            this value to `compute_function_objective()` in order to
            reset the problem's internal state.
        """

    @abstractmethod
    def compute_function_objective(
        self,
        cycle_time: float,
        params: ParamType,
    ) -> float:
        """Perform an optimization step.

        Args:
            cycle_time: The point in time at which the objective is
                being optimized. Typically measured in integer
                milliseconds from the start of a cycle in the machine.
            params: The parameters for which the loss shall be
                calculated. This must have the same structure as the
                space returned by `get_optimization_space()`. It should
                be within the bounds of the space, but if this is
                exactly the value returned by `get_initial_params()`, it
                might exceed them.

        Returns:
            The objective associated with these parameters, also known
            as loss or cost. Numerical optimizers may want to minimize
            this value.
        """

    def get_objective_function_name(self) -> str:
        """Return the name of the objective function, if any."""
        return ""

    def get_param_function_names(self) -> t.Sequence[str]:
        """Return the names of the functions being modified."""
        return ()

    def override_skeleton_points(self) -> t.Sequence[float] | None:
        """Hook to let the problem choose the skeleton points.

        Note that returning an empty sequence means that there are no
        suitable skeleton points. To leave the choice to the user,
        return the default value of None instead.
        """
        return None
