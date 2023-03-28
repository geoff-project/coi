"""An interface that supports RL and numerical optimization."""

# pylint: disable = abstract-method, too-few-public-methods

import typing as t
from abc import ABCMeta, abstractmethod

import gym
import numpy

from ._problem import Problem

if t.TYPE_CHECKING:  # pragma: no cover
    # pylint: disable = unused-import
    import scipy.optimize

Constraint = t.Union[
    "scipy.optimize.LinearConstraint", "scipy.optimize.NonlinearConstraint"
]


class SingleOptimizable(Problem, metaclass=ABCMeta):
    """Interface for single-objective numerical optimization.

    Fundamentally, an environment (described by :class:`gym.Env`)
    contains a hidden *state* on which *actions* can be performed. Each
    action causes a *transition* from one state to another. Each
    transition produces an *observation* and a *reward*.

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
        optimization_space: A :class:`~gym.spaces.Space` instance that
            describes the phase space of parameters. This may be the
            same or different from the :attr:`~gym.Env.action_space`.
            This attribute is required.
        objective_range: Optional. Specifies the range in which the
            return value of :meth:`compute_single_objective()` will lie.
            The default is to allow any finite float value, but
            subclasses may restrict this e.g. for normalization
            purposes.
        objective_name: Optional. A custom name for the objective
            function. You should only set this attribute if there is a
            physical meaning to the objective. The default is not to
            attach any meaning to the objective function.
        param_names: Optional. Custom names for each of the parameters
            of the problem. If set, this list should have exactly as
            many elements as the :attr:`optimization_space`. The default
            is not to attach any meaning to the individual parameters.
        constraints: Optional. The constraints that apply to this
            optimization problem. For now, each constraint must be
            either a :class:`~scipy.optimize.LinearConstraint` or a
            :class:`~scipy.optimize.NonlinearConstraint`. In the future,
            this might be relaxed to allow more optimization algorithms.
        constraint_names: Optional. Custom names for each of the
            :attr:`constraints` of the problem. If set, this list should
            have exactly as many elements as the :attr:`constraints`.
            The default is not to attach any meaning to the constraints.
    """

    optimization_space: gym.spaces.Space = None
    objective_range: t.Tuple[float, float] = (-float("inf"), float("inf"))
    objective_name: str = ""
    param_names: t.List[str] = []
    constraints: t.List[Constraint] = []
    constraint_names: t.List[str] = []

    @abstractmethod
    def get_initial_params(self) -> numpy.ndarray:
        """Return an initial set of parameters for optimization.

        The returned parameters should be within the optimization space,
        i.e. ``opt.get_initial_params() in opt.optimization_space``
        should be True.

        This method is similar to :meth:`~gym.Env.reset()` but is
        allowed to always return the same value; or to skip certain
        calculations, in the case of problems that are expensive to
        evalaute.
        """
        raise NotImplementedError()  # pragma: no cover

    @abstractmethod
    def compute_single_objective(self, params: numpy.ndarray) -> float:
        """Perform an optimization step.

        This function is similar to :meth:`~gym.Env.step()`, but it
        accepts parameters instead of an action. See the class docstring
        for the difference.

        This function may modify the environment, but it should
        fundamentally be stateless: Calling it twice with the same
        parameters should return the same loss, excepting any stochastic
        noise.

        Args:
            params: The parameters for which the loss shall be
                calculated. This should be within, but must at least
                have the same structure, as :attr:`optimization_space`.

        Returns:
            The loss associated with these parameters. Numerical
            optimizers may want to minimize that loss.
        """
        raise NotImplementedError()  # pragma: no cover
