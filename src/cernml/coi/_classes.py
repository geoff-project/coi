# SPDX-FileCopyrightText: 2020-2024 CERN
# SPDX-FileCopyrightText: 2023-2024 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

"""These are the most prominent classes provided by this package.

They provide an extension of the API provided by :doc:`Gymnasium
<gym:README>` and are heavily inspired by it. They are in turn:

- `~.coi.Problem`: The root of the interface hierarchy. Both the
  following two classes _and_ `.coi.Env` are subclasses of it.
- `~.coi.SingleOptimizable`: an `.coi.Env`-like class for numerical
  optimization problems;
- `~.coi.FunctionOptimizable`: A variant of `~.coi.SingleOptimizable`
  for situations where a *function* over time must be optimized
  pointwise in order. This is the case e.g. when adjusting the tune of
  a circular particle accelerator.
- `~.coi.HasNpRandom`: A mix-in class that provides a convenient
  random-number generator (RNG). Already included by `~.coi.Problem`.
- `.CustomOptimizerProvider`: An optional mix-in interface for
  optimization problems that require a specific optimization algorithm
  to be solved.

Each of these three classes is an :term:`abstract base class` (ABC). In
short, this means that they can be superclasses of other classes, even
if the latter don't inherit from them. The only requirement is that the
subclass provides the same members as the ABC. This follows and extends
the idea of structural subtyping implemented by `typing.Protocol`.

    >>> from cernml.coi import Problem
    >>> class MyClass:
    ...     metadata = {}
    ...     render_mode = None
    ...     spec = None
    ...     @property
    ...     def unwrapped(self):
    ...         return self
    ...     def close(self):
    ...         pass
    ...     def render(self):
    ...         raise NotImplementedError
    ...     def get_wrapper_attr(self, name):
    ...         return getattr(self, name)
    >>> issubclass(MyClass, Problem)
    True

In practice, you still want to subclass these ABCs because they provide
some conveniences that are bothersome to implement otherwise. See
`~.coi.Problem` for a list.
"""

from __future__ import annotations

import typing as t
import warnings
from abc import ABCMeta, abstractmethod
from types import MappingProxyType

import numpy as np
from gymnasium import Env
from gymnasium.spaces import Space
from gymnasium.utils import seeding

from . import protocols
from ._machine import Machine
from .protocols import Constraint, ParamType
from .registration import errors

if t.TYPE_CHECKING:
    import gymnasium.envs.registration
    from typing_extensions import Self

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


class HasNpRandom:
    """Mixin that replicates the `gymnasium.Env.np_random` property.

    This abstracts the property in a generalized fashion. The `Problem`
    base class subclasses it for convenience.
    """

    _np_random: np.random.Generator | None = None

    @property
    def np_random(self) -> np.random.Generator:
        """The problem's internal random number generator.

        On its first access, the generator is lazily initialized with
        a random seed. This property is writeable to support
        initialization with a fixed seed. Typically, this is done within
        `~SingleOptimizable.get_initial_params()` and
        :func:`~gymnasium.Env.reset()`, which simply accept a *seed*
        parameter.
        """
        if self._np_random is None:
            self._np_random, _ = seeding.np_random()
        return self._np_random

    @np_random.setter
    def np_random(self, value: np.random.Generator) -> None:
        self._np_random = value


@protocols.Problem.register
class Problem(HasNpRandom, metaclass=ABCMeta):
    """Root base class for all optimization problems.

    You typically don't subclass this class directly. Instead, subclass
    one of its subclasses, e.g. `Env` or `SingleOptimizable`. This class
    exists for two purposes:

    - define which parts of the interfaces are common to all of them;
    - provide an easy way to test whether an interface is compatible
      with the generic optimization framework.

    This is an :term:`abstract base class`. This means even classes that
    don't inherit from it may be considered a subclass. To be considered
    a subclass, a class must provide:

    - the attributes `metadata`, `render_mode` and `spec`;
    - provide the methods `render()`, `close()` and
      `get_wrapper_attr()`;
    - a dynamic property `unwrapped`.

    While this is all that is necessary to be considered a subclass,
    direct inheritance provides the following additional benefits:

    - Its ``__init__()`` method requires *render_mode*, verifies it with
      the ``"render_modes"`` key of `metadata` and assigns it to the
      `render_mode` attribute. This reduces the amount of boilerplate
      code you have to write yourself.
    - It implements the :term:`context manager` protocol to
      automatically call `close()` when the user is done with a problem.
    - It provides the `np_random` property as an exclusive and lazily
      initialized random-number generator for the problem.
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
    """The capabilities and behavior of this problem. This should be
    a class-level constant attribute. It must be a mapping with
    string-type keys. Instances may replace this dict with a custom one,
    but they should never modify the existing dict. It communicates
    fundamental properties of the class and how a host application can
    use it.

    The following keys are defined and understood by this
    package:

    ``"render_modes"``
        The render modes that the optimization problem
        understands. Standard render modes are documented under
        `render()`. This replaces the deprecated key
        ``"render.modes"`` with the same meaning.
    ``"cern.machine"``
        The accelerator that an optimization problem is
        associated with. This must be a value of type `Machine`.
    ``"cern.japc"``
        A boolean flag indicating that the problem's constructor
        expects an argument named *japc* of type
        :class:`~pyjapc.PyJapc`. Enable it if your class
        performs any machine communication via JAPC. Do not
        create your own :class:`~pyjapc.PyJapc` instance. Among
        other things, this ensures that the correct timing
        selector is set.
    ``"cern.cancellable"``
        A boolean flag indicating that the problem's constructor
        expects an argument named *cancellation_token* of type
        `~cernml.coi.cancellation.Token`. Enable it if your
        class ever enters any long-running loops that the user
        may want to interrupt. A classic example is the
        acquisition and validation of cycle-bound data.

    Additionally, all keys that start with ``"cern."`` are
    reserved for future use.
    """

    render_mode: str | None = None
    """The chosen render mode. This is expected to be set inside
    ``__init__()`` and not changed again afterwards. The value should be
    either None (which implies no rendering) or one of the strings in
    ``metadata["render_modes"]``. Standard render modes are documented
    under `render()`."""

    # HACK: We say this is a Gym EnvSpec, but in fact it will almost
    # always be a COI EnvSpec. This is so that `OptEnv` can be
    # a subclass of both `gym.Env` and `coi.SingleOptimizable` without
    # conflicts.
    #
    # The two spec classes are nearly identical and Gym's specs are
    # a virtual subclass of the COI's. If it is important to you to get
    # the typing of this attribute right, use `coi.protocols.Problem`
    # as annotation instead of this class.
    spec: gymnasium.envs.registration.EnvSpec | None = None
    """Information on how the problem was initialized. This is set by
    `make()` and you are not expected to modify it yourself. Wrappers
    should :func:`~copy.deepcopy()` the spec of the wrapped environment
    and make their modifications on the copy."""

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

    def __enter__(self) -> Self:
        return self

    # pylint: disable = useless-return
    def __exit__(self, *args: object) -> bool | None:
        self.close()
        return None

    # pylint: enable = useless-return

    def close(self) -> None:
        """Perform any necessary cleanup.

        This method may be overridden to perform cleanup that does not
        happen automatically. Examples include stopping JAPC
        subscriptions or canceling any spawned threads. By default, this
        method does nothing.

        After this method has been called, no further methods may be
        called on the problem, with the following exceptions:

        - `get_wrapper_attr()` must continue to behave as expected;
        - `unwrapped` must continue to behave as expected;
        - calling `close()` again should do nothing.
        """
        return None  # noqa: RET501

    def render(self) -> t.Any:
        """Render the environment according to the `render_mode`.

        The set of supported modes varies. Some problems do not support
        rendering at all. See :func:`gymnasium.Env.render()` for a list
        of render modes standardized by Gymnasium.

        This package currently standardizes one additional render mode:

        ``"matplotlib_figures"``
            Render to one or more :class:`~matplotlib.figure.Figure`
            objects. This should return all figures whose contents have
            changed. The following return types are allowed:

            - a single :class:`~matplotlib.figure.Figure` object;
            - an iterable of bare :class:`~matplotlib.figure.Figure`
              objects or 2-tuples of `str` and
              :class:`~matplotlib.figure.Figure` or both;
            - a mapping with `str` keys and
              :class:`~matplotlib.figure.Figure` values.

            Strings are interpreted as window titles for their
            associated figure.

        Example:

            >>> from gymnasium import Env
            >>> class MyEnv(Env):
            ...     metadata = {'render_modes': ['human', 'rgb_array']}
            ...     def render(self, mode='human'):
            ...         if mode == 'rgb_array':
            ...             # Return RGB frame suitable for video.
            ...             return np.array(...)
            ...         if mode == 'human':
            ...             # Pop up a window and render.
            ...             pyplot.plot(...)
            ...             pyplot.show()
            ...             return None
            ...         # just raise an exception
            ...         return super().render(mode)

        Note:
            Make sure to declare all modes that you support in the
            ``"render_modes"`` key of your `metadata`. It's recommended
            to call `super` in implementations to use the functionality
            of this method.
        """
        assert True
        raise NotImplementedError

    @property
    def unwrapped(self) -> protocols.Problem:
        """Return the core problem.

        By default, this just returns *self*. However, :doc:`environment
        wrappers <gym:api/wrappers>` override this method to instead
        return the wrapped problem (recursively, if necessary).

        Example:

            >>> class Concrete(Problem):
            ...     pass
            >>> class Wrapper(Problem):
            ...     def __init__(self, wrapped):
            ...         self._wrapped = wrapped
            ...     @property
            ...     def unwrapped(self):
            ...         # Note the recursion.
            ...         return self._wrapped.unwrapped
            >>> inner = Concrete()
            >>> outer = Wrapper(inner)
            >>> inner.unwrapped is inner
            True
            >>> outer.unwrapped is inner
            True
        """
        return self

    def get_wrapper_attr(self, name: str) -> t.Any:
        """Get the attribute *name* from the environment."""
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
    """Interface for single-objective numerical optimization.

    Typically, an RL environment (described by `.Env`) contains a hidden
    *state* on which *actions* can be performed. Each *action* changes
    the *state* and produces an *observation* and a *reward*. In
    contrast, an optimization problem has certain *parameters* that can
    be *set* to given values. Each set of values (and not the transition
    between them) is associated with a *objective value* that shall be
    minimized.

    This means in short:

    - **actions** describe a *step* that shall be taken in the phase
      space of states;
    - **parameters** describe the *point* in phase space to move to.

    A parameter may be e.g. the electric current supplied to a magnet,
    and an action may be the value by which to increase or decrease that
    current. The difference between the parameters and the hidden state
    is that the parameters may describe only a *subset* of the state.
    There may be state variables that cannot be influenced by the
    optimizer.

    Like `Problem`, this is an :term:`abstract base class`. While you
    need not inherit from it directly, doing so provides the following
    benefits:

    - correct default values for all optional attributes;
    - `get_initial_params()` correctly handles the *seed* argument and
      seeds `~Problem.np_random` if it is passed.
    - ``__init__()`` handles *render_mode* correctly;
    - the :term:`context manager` protocol to automatically call
      `~Problem.close()`;
    - a property `~Problem.np_random` for convenient random-number
      generation.
    """

    optimization_space: Space[ParamType]
    """A `Space` instance that describes the phase space of parameters.
    This may be the same or different from the
    `~gymnasium.Env.action_space`. This attribute is required."""

    constraints: t.Sequence[Constraint] = ()
    """Optional. The constraints that apply to this optimization
    problem. For now, each constraint must be either
    a `~scipy.optimize.LinearConstraint` or
    a `~scipy.optimize.NonlinearConstraint`. In the future, this might
    be relaxed to allow more optimization algorithms."""

    objective_name: str = ""
    """Optional. A custom name for the objective function. You should
    only set this attribute if there is a physical meaning to the
    objective. By default, host applications should pick a neutral name
    like "objective function"."""

    param_names: t.Sequence[str] = ()
    """Optional. Custom names for each of the parameters of the problem.
    If set, this list should have exactly as many elements as the
    `optimization_space`. By default, host applications should pick
    neutral names, e.g. "Parameter 1…N"."""

    constraint_names: t.Sequence[str] = ()
    """Optional. Custom names for each of the `constraints` of the
    problem. If set, this list should have exactly as many elements as
    the `constraints`. By default, host applications should pick neutral
    names, e.g. "Constraint 1…N"."""

    @abstractmethod
    def get_initial_params(
        self, *, seed: int | None = None, options: dict[str, t.Any] | None = None
    ) -> ParamType:
        """Return an initial set of parameters for optimization.

        This method is similar to :func:`~gymnasium.Env.reset()` but is
        allowed to always return the same value; or to skip certain
        calculations, in the case of problems that are expensive to
        evaluate.

        Args:
            seed: Optional. If passed, this should be used to initialize
                the problem's internal random-number generator. Passing
                this argument should lead to predictable behavior of the
                problem. If this is not possible, you should set the
                `nondeterministic <.coi.register>` when registering your
                problem.
            options: Optional. Environments may choose to extract
                additional information about resets from this argument.

        Returns:
            A set of parameters suitable to be passed to
            `compute_single_objective()`. It should lie within the
            problem's `optimization_space`. Nonetheless, hosts should
            verify whether this is indeed the case.

        Warning:
            If the return value lies outside of the given optimization
            space, and a host application wishes to reset the problem to
            its original state, it may choose to call
            `compute_single_objective()` with that return value even
            though it is out of bounds. Thus, it is *crucial* to ensure
            that initial value and optimization space match.
        """
        if seed is not None:
            self._np_random, _ = seeding.np_random(seed)
        return  # type: ignore[return-value]

    @abstractmethod
    def compute_single_objective(self, params: ParamType) -> t.SupportsFloat:
        """Perform an optimization step.

        This function is similar to :func:`~gymnasium.Env.step()`, but
        it accepts parameters instead of an action. See the class
        docstring for the difference.

        This function may modify the environment, but it should
        conceptually be stateless: Calling it twice with the same
        parameters should return the same objective value plus
        stochastic noise. On real machines, this is rarely the case due
        to machine drift and other external effects.

        Args:
            params: The parameters for which the objective shall be
                calculated. This must have the same shape as
                `optimization_space`. It must further be *within* that
                space. However, if `get_initial_params()` returns an
                out-of-bounds value, that value may also be passed to
                this method.

        Returns:
            The *objective* value associated with these parameters.
            Numerical optimizers may want to minimize this objective. It
            is often also called *cost* or *loss*.
        """
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
    """Interface for problems that optimize functions over time.

    An optimization problem in which the target is a function over time
    that is being optimized at multiple *skeleton points* should
    implement this interface instead of `SingleOptimizable`. This
    interface allows passing through the skeleton points as parameters
    called *cycle_time*. The name "cycle" is inspired by the fact that
    this problem comes up most often in the context of optimizing
    synchrotron parameters that change during a fill-accelerate-extract
    cycle. In this case, *cycle_time* implies that it is measured from
    the start of the cycle, rather than e.g. the start of injection.

    Like `Problem`, this is an :term:`abstract base class`. While you
    need not inherit from it directly, doing so provides the following
    benefits:

    - correct default values for all optional attributes, and default
      implementations for optional methods;
    - `get_initial_params()` correctly handles the *seed* argument and
      seeds `~Problem.np_random` if it is passed.
    - ``__init__()`` handles *render_mode* correctly;
    - the :term:`context manager` protocol to automatically call
      `~Problem.close()`;
    - a property `~Problem.np_random` for convenient random-number
      generation.
    """

    constraints: t.Sequence[Constraint] = ()
    """The constraints that apply to this optimization problem. For now,
    each constraint must be either
    a :class:`~scipy.optimize.LinearConstraint` or
    a :class:`~scipy.optimize.NonlinearConstraint` as provided by
    :mod:`scipy.optimize`. In the future, this might be relaxed to allow
    more optimization algorithms."""

    @abstractmethod
    def get_optimization_space(self, cycle_time: float) -> Space[ParamType]:
        """Return the optimization space for a given point in time.

        This should return a `.Space` instance that describes the phase
        space of parameters. While one would typically expect this phase
        space to be constant for all points on the function that is to
        be optimized, there are cases where this is not true.

        Trivially, one can imagine a ramping function where the range of
        allowed values in the flat bottom is smaller than at the flat
        top.

        Nonetheless, all returned spaces should still have the same
        *shape*.
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

        This method is similar to :func:`~gymnasium.Env.reset()` but is
        allowed to always return the same value; or to skip certain
        calculations, in the case of problems that are expensive to
        evaluate.

        Args:
            cycle_time: The point in time at which the objective is
                being optimized.
            seed: Optional. If passed, this should be used to initialize
                the problem's internal random-number generator. Passing
                this argument should lead to predictable behavior of the
                problem. If this is not possible, you should set the
                `nondeterministic <.coi.register>` when registering your
                problem.
            options: Optional. Environments may choose to extract
                additional information about resets from this argument.

        Returns:
            A set of parameters suitable to be passed to
            `compute_function_objective()` with the same *cycle_time*.
            It should lie within the space returned by
            `get_optimization_space()` for this *cycle_time*.
            Nonetheless, hosts should verify whether this is indeed the
            case.

        Warning:
            If the return value lies outside of the given optimization
            space, and a host application wishes to reset the problem to
            its original state, it may choose to call
            `compute_function_objective()` with that return value even
            though it is out of bounds. Thus, it is *crucial* to ensure
            that initial value and optimization space match.
        """
        if seed is not None:
            self._np_random, _ = seeding.np_random(seed)
        return  # type: ignore[return-value]

    @abstractmethod
    def compute_function_objective(self, cycle_time: float, params: ParamType) -> float:
        """Perform an optimization step at the given point in time.

        This function is the core of the interface. When called, it
        should perform the following steps:

        1. Convert *params* into a format suitable for communication
           with the machine; this may include applying offsets, scaling
           factors, etc.
        2. Send the new settings to the machine. The easiest way to do
           this is via :func:`cernml.lsa_utils.incorporate_and_trim()`.
        3. Receive new measurements from the machine based on the new
           settings. This may include some sort of waiting logic to
           ensure that the settings have propagated to the machine.
        4. Reduce the measurements into a scalar cost to be minimized.
           This may involve scaling, averaging over multiple variables
           and other transformations.

        This function may modify the environment, but it should
        conceptually be stateless: Calling it twice with the same
        parameters should return the same objective value plus
        stochastic noise. On real machines, this is rarely the case due
        to machine drift and other external effects.

        Args:
            cycle_time: The point in time at which the objective is
                being optimized.
            params: The parameters for which the objective shall be
                calculated. This should be regarded as corrections on
                one or more functions over time.

        Returns:
            The *objective* value associated with these parameters and
            this *cycle_time*. Numerical optimizers may want to minimize
            this objective. It is often also called *cost* or *loss*.
        """
        raise NotImplementedError

    def get_objective_function_name(self) -> str:
        """Return the name of the objective function.

        By default, this method returns None. If it returns a non-empty
        string, it should be the name of the objective function of this
        optimization problem. A host application may use this name e.g.
        to label a graph of the objective function's value as it is
        being optimized.
        """
        return ""

    def get_param_function_names(self) -> t.Sequence[str]:
        """Return the names of the functions being modified.

        By default, this method returns an empty list. If the list is
        non-empty, if should contain as many names as the corresponding
        box returned by `get_optimization_space()`. Each name should
        correspond to an LSA parameter that is being corrected by the
        optimization procedure.

        A host application may use these names to show the functions
        that are being modified to the user.
        """
        return ()

    def override_skeleton_points(self) -> t.Sequence[float] | None:
        """Hook to let the problem choose the skeleton points.

        You should only override this method if your problem cannot be
        solved well if optimized at arbitrary skeleton points. In such a
        case, this method allows you to handle the selection of skeleton
        points in a customized fashion in your own implementation of
        `~cernml.coi.Configurable`.

        If overridden, this function should return the list of skeleton
        points at which the problem should be evaluated. As always, each
        skeleton point should be given as a floating-point time in
        milliseconds since the beginning of an acceleration cycle. For
        maximum compatibility, it is suggested not to return fractional
        cycle times.

        A host application should call this method before starting an
        optimization run. If the return value is `None`, it may
        proceed to let the user choose the skeleton points at which to
        optimize. If the return value is a list, the user should be
        allowed to review, but not modify it. In that case, the other
        methods of this class must not be called with any skeleton point
        that is not in that list.
        """
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
