# SPDX-FileCopyrightText: 2020-2024 CERN
# SPDX-FileCopyrightText: 2023-2024 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

"""An interface that supports RL and numerical optimization."""

# pylint: disable = abstract-method, too-few-public-methods

import typing as t
from abc import abstractmethod

import gymnasium as gym

from ._problem import BaseProblem, Problem

if t.TYPE_CHECKING:
    # pylint: disable = unused-import
    import scipy.optimize  # noqa: F401, RUF100

__all__ = (
    "Constraint",
    "ParamType",
    "SingleOptimizable",
)

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

    optimization_space: gym.spaces.Space[ParamType]
    objective_range: tuple[float, float] = (-float("inf"), float("inf"))
    constraints: t.Sequence[Constraint] = []

    objective_name: str = ""
    param_names: t.Sequence[str] = ()
    constraint_names: t.Sequence[str] = ()

    # TODO: Add optional `seed` and `options` arguments.
    @abstractmethod
    def get_initial_params(self) -> ParamType:
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


@SingleOptimizable.register
class BaseSingleOptimizable(BaseProblem, t.Generic[ParamType]):
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

    optimization_space: gym.spaces.Space[ParamType]
    objective_range: tuple[float, float] = (-float("inf"), float("inf"))
    constraints: t.Sequence[Constraint] = []

    objective_name: str = ""
    param_names: t.Sequence[str] = []
    constraint_names: t.Sequence[str] = []

    # TODO: If `get_initial_params()` gains new arguments, those should
    # be used by default in this method.
    @abstractmethod
    def get_initial_params(self) -> ParamType:
        """See `SingleOptimizable.get_initial_params()`."""  # noqa: D402
        raise NotImplementedError

    @abstractmethod
    def compute_single_objective(self, params: ParamType) -> t.SupportsFloat:
        """See `SingleOptimizable.compute_single_objective()`."""  # noqa: D402
        raise NotImplementedError
