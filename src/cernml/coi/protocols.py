# SPDX-FileCopyrightText: 2020-2024 CERN
# SPDX-FileCopyrightText: 2023-2024 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

"""Provide protocols for the core interfaces of this package."""

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
    "ParamType",
    "Problem",
    "SingleOptimizable",
    "Space",
)


@t.runtime_checkable
class HasNpRandom(AttrCheckProtocol, t.Protocol):
    """Protocol for classes that manage their own RNG.

    This abstracts out the `gymnasium.Env.np_random` property. The
    `Problem` protocol does not depend on it, but the :term:`abstract
    base class` `BaseProblem` subclasses it as a mixin for convenience.
    """

    np_random: np.random.Generator


@t.runtime_checkable
class Problem(AttrCheckProtocol, t.Protocol):
    """Root protocol for all optimization problems.

    Do not not directly subclass this protocol. Instead, derive from one
    of its subclasses like `~gym.Env` or `SingleOptimizable`. This class
    exists for two purposes:

    - define which parts of the interfaces are common to all of them;
    - provide an easy way to test whether an interface is compatible
      with the generic optimization framework.

    This is a `~typing.Protocol`. This means even classes that don't
    inherit from it may be considered a subclass. To be considered
    a subclass, a class must merely:

    - provide the methods `render()`, `close()` and
      `get_wrapper_attr()`;
    - provide a dynamic property `unwrapped`;
    - provide the attributes `render_mode` and `spec`.

    Attributes:
        metadata: Capabilities and behavior of this problem.

            This must be a class-level constant attribute. It must be a
            mapping with string-type keys. Instances must not
            dynamically modify or overwrite this dict. It communicates
            fundamental properties of the class and how a host
            application can use it.

            The following keys are defined and understood by this
            package:

            ``"render_modes"``
                The render modes that the optimization problem
                understands. Standard render modes are documented under
                `render()`.
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

    @property
    def render_mode(self) -> str | None:
        """The render mode as determined during initialization.

        This attribute is expected to be set inside ``__init__()`` and
        then not changed again.
        """
        # Hack: We mark this as read-only here, but all sub-protocols
        # make it writeable again. The reason is that
        # `gymnasium.Wrapper` defines `render_mode` to be read-only. If
        # it were settable in `Problem`, wrappers would no longer
        # considered to implement the protocol.
        return vars(self).get("render_mode")

    @property
    def spec(self) -> MinimalEnvSpec | None:
        """Information on how the problem was initialized.

        This property is usually set by `make()`. You generally should
        not modify it yourself. Wrappers should `~copy.deepcopy()` the
        spec of the wrapped environment and make their modifications on
        the copy.
        """
        # Hack: We mark this as read-only here, but all sub-protocols
        # make it writeable again.
        # Marking the attribute as read-only also makes it _covariant_,
        # i.e. subclasses are allowed to return subclasses of
        # `MinimalEnvSpec` instead of `MinimalEnvSpec` _exactly_. This
        # allows us to replace `gymnasium.envs.registration.EnvSpec`
        # with `cernml.coi.registration.EnvSpec`, which is exactly the
        # same except it calls _our_ `make()` instead of Gymnasium's.
        return vars(self).get("spec")

    def close(self) -> None:
        """Perform any necessary cleanup.

        This method may be overridden to perform cleanup that does not
        happen automatically. Examples include stopping JAPC
        subscriptions or canceling any spawned threads. By default, this
        method does nothing.

        After this method has been called, no further methods may be
        called on the problem, with the following exceptions:

        - `unwrapped` must continue to behave as expected;
        - calling `close()` again should do nothing.
        """
        return None  # noqa: RET501

    @property
    def unwrapped(self) -> "Problem":
        """Return the core problem.

        By default, this just returns *self*. However, if this class
        is a wrapper around another problem (which might, in turn, also
        be a wrapper), it should return that problem recursively.

        This exists to support the :class:`gym.Wrapper` design pattern.

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

    def render(self) -> t.Any:
        """Render the environment.

        Args:
            mode: the mode to render with. Must be a member of
                ``self.metadata["render_modes"]``.

        The set of supported modes varies. Some problems do not support
        rendering at all. The following modes have a standardized
        meaning:

        ``"human"``
            Render to the current display or terminal and return
            nothing. Usually for human consumption. Valid
            implementations open a Matplotlib or Pyglet window and
            return immediately.
        ``"rgb_array"``
            Return an numpy.ndarray with shape ``(x, y, 3)``,
            representing RGB values for an *x*-by-*y* pixel image,
            suitable for turning into a video.
        ``"ansi"``
            Return a `str` or `io.StringIO` containing a terminal-style
            text representation. The text can include newlines and ANSI
            escape sequences (e.g. for colors).
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
        # pylint: disable = unused-argument
        # Make PyLint realize that this method is not abstract. We do
        # allow people to not override this method in their subclass.
        # However, PyLint thinks that any method that raises
        # NotImplementedError should be overridden.
        assert True
        raise NotImplementedError

    def get_wrapper_attr(self, name: str) -> t.Any:
        """Gets the attribute `name` from the environment."""
        return getattr(self, name)


Constraint = t.Union[
    "scipy.optimize.LinearConstraint", "scipy.optimize.NonlinearConstraint"
]

ParamType = t.TypeVar("ParamType")  # pylint: disable = invalid-name


@t.runtime_checkable
class SingleOptimizable(Problem, t.Protocol[ParamType]):
    """Interface for single-objective numerical optimization.

    Fundamentally, an environment (described by `gym.Env`) contains a
    hidden *state* on which *actions* can be performed. Each action
    causes a *transition* from one state to another. Each transition
    produces an *observation* and a *reward*.

    In contrast, an *optimizable* problem has certain *parameters* that
    can be *set* to transition *into* a certain state. Each state (not
    the transition!) is associated with a *loss* that shall be
    minimized.

    The difference between actions and parameters is:

    - **actions** describe a *step* that shall be taken in the phase
      space of states;
    - **parameters** describe the *point* in phase space that shall be
      moved to.

    A parameter may be e.g. the electric current supplied to a magnet,
    and an action may be the value by which to increase or decrease that
    current.

    The difference between the parameters and the hidden state is that
    the parameters may describe only a *subset* of the state. There may
    be state variables that cannot be influenced by the optimizer.

    Attributes:
        optimization_space: A `~gym.spaces.Space` instance that
            describes the phase space of parameters. This may be the
            same or different from the `~gym.Env.action_space`. This
            attribute is required.
        objective_range: Optional. Specifies the range in which the
            return value of `compute_single_objective()` will lie. The
            default is to allow any finite float value, but subclasses
            may restrict this e.g. for normalization purposes.
        objective_name: Optional. A custom name for the objective
            function. You should only set this attribute if there is a
            physical meaning to the objective. The default is not to
            attach any meaning to the objective function.
        param_names: Optional. Custom names for each of the parameters
            of the problem. If set, this list should have exactly as
            many elements as the `optimization_space`. The default is
            not to attach any meaning to the individual parameters.
        constraints: Optional. The constraints that apply to this
            optimization problem. For now, each constraint must be
            either a :class:`~scipy.optimize.LinearConstraint` or a
            :class:`~scipy.optimize.NonlinearConstraint`. In the future,
            this might be relaxed to allow more optimization algorithms.
        constraint_names: Optional. Custom names for each of the
            `constraints` of the problem. If set, this list should have
            exactly as many elements as the `constraints`. The default
            is not to attach any meaning to the constraints.
    """

    render_mode: str | None = None

    optimization_space: Space[ParamType]
    objective_range: tuple[float, float] = (-float("inf"), float("inf"))
    constraints: t.Sequence[Constraint] = []

    objective_name: str = ""
    param_names: t.Sequence[str] = ()
    constraint_names: t.Sequence[str] = ()

    @abstractmethod
    def get_initial_params(
        self, *, seed: int | None = None, options: dict[str, t.Any] | None = None
    ) -> ParamType:
        """Return an initial set of parameters for optimization.

        The returned parameters should be within the optimization space,
        i.e. ``opt.get_initial_params() in opt.optimization_space``
        should be True.

        This method is similar to `~gym.Env.reset()` but is allowed to
        always return the same value; or to skip certain calculations,
        in the case of problems that are expensive to evalaute.
        """
        raise NotImplementedError

    @abstractmethod
    def compute_single_objective(self, params: ParamType) -> t.SupportsFloat:
        """Perform an optimization step.

        This function is similar to `~gym.Env.step()`, but it accepts
        parameters instead of an action. See the class docstring for the
        difference.

        This function may modify the environment, but it should
        fundamentally be stateless: Calling it twice with the same
        parameters should return the same loss, excepting any stochastic
        noise.

        Args:
            params: The parameters for which the loss shall be
                calculated. This should be within, but must at least
                have the same structure, as `optimization_space`.

        Returns:
            The loss associated with these parameters. Numerical
            optimizers may want to minimize that loss.
        """
        raise NotImplementedError


@t.runtime_checkable
class FunctionOptimizable(Problem, t.Protocol[ParamType]):
    """Interface for problems that optimize functions over time.

    An optimization problem in which the target is a function over time
    that is being optimized at multiple *skeleton points* should
    implement this interface instead of `SingleOptimizable`. This
    interface allows passing through the skeleton points as parameters
    called *cycle_time*. The part "cycle" is important to signify that
    time is measured from the beginning of the cycle; some measuring
    equipment measures time from the beginning of injection instead.

    Attributes:
        objective_range: Specifies the range in which the return value
            of `compute_function_objective()` will lie. The default is
            to allow any float value, but subclasses may restrict this
            e.g. for normalization purposes.
        constraints: The constraints that apply to this optimization
            problem. For now, each constraint must be either a
            :class:`~scipy.optimize.LinearConstraint` or a
            :class:`~scipy.optimize.NonlinearConstraint` as provided by
            :mod:`scipy.optimize`. In the future, this might be relaxed
            to allow more optimization algorithms.
    """

    render_mode: str | None = None

    objective_range: tuple[float, float] = (-np.inf, np.inf)
    constraints: t.Sequence[Constraint] = []

    @abstractmethod
    def get_optimization_space(self, cycle_time: float) -> Space[ParamType]:
        """Return the optimization space for a given point in time.

        This should return a `~gym.spaces.Space` instance that describes
        the phase space of parameters. While one would typically expect
        this phase space to be constant for all points on the function
        that is to be optimized, there are cases where this is not true.

        Trivially, one can imagine a ramping function where the range of
        allowed values in the flat bottom is smaller than at the flat
        top.
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

        The returned parameters should be within the optimization space
        that has been returned from `get_optimization_space()` for the
        same time. In other words, the following assert should never
        raise an exception:

            >>> def trivial(opt: FunctionOptimizable, time: float):
            ...     space = opt.get_optimization_space(time)
            ...     params = opt.get_initial_params(time)
            ...     assert params in space

        This method is similar to `gym.Env.reset()` but is allowed to
        always return the same value; or to skip certain calculations,
        in the case of problems that are expensive to evalaute.

        Args:
            cycle_time: The point in time at which the objective is
                being optimized.

        Returns:
            The initial parameters.
        """
        raise NotImplementedError

    @abstractmethod
    def compute_function_objective(
        self,
        cycle_time: float,
        params: ParamType,
    ) -> float:
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
        fundamentally be stateless: Calling it twice with the same
        parameters should return the same loss, excepting any stochastic
        noise.

        Args:
            cycle_time: The point in time at which the objective is
                being optimized.
            params: The parameters for which the loss shall be
                calculated. This should be regarded as corrections on
                one or more functions over time.

        Returns:
            The loss associated with these parameters. Numerical
            optimizers may want to minimize that loss.
        """
        raise NotImplementedError

    def get_objective_function_name(self) -> str | None:
        """Return the name of the objective function.

        By default, this method returns the empty string. If it returns
        a non-empty string, it should be the name of the objective
        function of this optimization problem. A host application may
        use this name e.g. to label a graph of the objective function's
        value as it is being optimized.
        """
        return None

    def get_param_function_names(self) -> list[str]:
        """Return the names of the functions being modified.

        By default, this method returns an empty list. If the list is
        non-empty, if should contain as many names as the corresponding
        box returned by `get_optimization_space()`. Each name should
        correspond to an LSA parameter that is being corrected by the
        optimization procedure.

        A host application may use these names to show the functions
        that are being modified to the user.
        """
        return []

    def override_skeleton_points(self) -> list[float] | None:
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
