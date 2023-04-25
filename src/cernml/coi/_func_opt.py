"""Definition of the interface for temporal optimization."""

import typing as t
from abc import ABCMeta, abstractmethod

import numpy as np

from ._problem import Problem
from ._single_opt import Constraint

if t.TYPE_CHECKING:
    from gym import Space  # pragma: no cover


class FunctionOptimizable(Problem, metaclass=ABCMeta):
    """Interface for problems that optimize functions over time.

    An optimization problem in which the target is a function over time
    that is being optimized at multiple *skeleton points* should
    implement this interface instead of :class:`SingleOptimizable`.
    This interface allows passing through the skeleton points as
    parameters called *cycle_time*. The part "cycle" is important to
    signify that time is measured from the beginning of the cycle; some
    measuring equipment measures time from the beginning of injection
    instead.

    Attributes:
        objective_range: Specifies the range in which the return value
            of :meth:`compute_function_objective()` will lie. The
            default is to allow any float value, but subclasses may
            restrict this e.g. for normalization purposes.
        constraints: The constraints that apply to this optimization
            problem. For now, each constraint must be either a
            :class:`~scipy.optimize.LinearConstraint` or a
            :class:`~scipy.optimize.NonlinearConstraint` as provided by
            :mod:`scipy.optimize`. In the future, this might be relaxed
            to allow more optimization algorithms.
    """

    objective_range: t.Tuple[float, float] = (-np.inf, np.inf)
    constraints: t.List[Constraint] = []

    @abstractmethod
    def get_optimization_space(self, cycle_time: float) -> "Space":
        """Return the optimization space for a given point in time.

        This should return a :class:`~gym.spaces.Space` instance that
        describes the phase space of parameters. While one would
        typically expect this phase space to be constant for all points
        on the function that is to be optimized, there are cases where
        this is not true.

        Trivially, one can imagine a ramping function where the range of
        allowed values in the flat bottom is smaller than at the flat
        top.
        """
        raise NotImplementedError()  # pragma: no cover

    @abstractmethod
    def get_initial_params(self, cycle_time: float) -> np.ndarray:
        """Return an initial set of parameters for optimization.

        The returned parameters should be within the optimization space
        that has been returned from `get_optimization_space` for the
        same time. In other words, the following assert should never
        raise an exception:

            >>> def trivial(opt: FunctionOptimizable, time: float):
            ...     space = opt.get_optimization_space(time)
            ...     params = opt.get_initial_params(time)
            ...     assert params in space

        This method is similar to :meth:`gym.Env.reset()` but is allowed
        to always return the same value; or to skip certain
        calculations, in the case of problems that are expensive to
        evalaute.

        Args:
            cycle_time: The point in time at which the objective is
                being optimized.

        Returns:
            The initial parameters.
        """
        raise NotImplementedError()  # pragma: no cover

    @abstractmethod
    def compute_function_objective(
        self, cycle_time: float, params: np.ndarray
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
        raise NotImplementedError()  # pragma: no cover

    def get_objective_function_name(self) -> t.Optional[str]:
        """Return the name of the objective function.

        By default, this method returns the empty string. If it returns
        a non-empty string, it should be the name of the objective
        function of this optimization problem. A host application may
        use this name e.g. to label a graph of the objective function's
        value as it is being optimized.
        """
        return None

    def get_param_function_names(self) -> t.List[str]:
        """Return the names of the functions being modified.

        By default, this method returns an empty list. If the list is
        non-empty, if should contain as many names as the corresponding
        :attr:`optimization_space`. Each name should correspond to an
        LSA parameter that is being corrected by the optimization
        procedure.

        A host application may use these names to show the functions
        that are being modified to the user.
        """
        return []

    def override_skeleton_points(self) -> t.Optional[t.List[float]]:
        """Hook to let the problem choose the skeleton points.

        You should only override this method if your problem cannot be
        solved well if optimized at arbitrary skeleton points. In such a
        case, this method allows you to handle the selection of skeleton
        points in a customized fashion in your own implementation of
        :class:`~cernml.coi.Configurable`.

        If overridden, this function should return the list of skeleton
        points at which the problem should be evaluated. As always, each
        skeleton point should be given as a floating-point time in
        milliseconds since the beginning of an acceleration cycle. For
        maximum compatibility, it is suggested not to return fractional
        cycle times.

        A host application should call this method before starting an
        optimization run. If the return value is :any:`None`, it may
        proceed to let the user choose the skeleton points at which to
        optimize. If the return value is a list, the user should be
        allowed to review, but not modify it. In that case, the other
        methods of this class must not be called with any skeleton point
        that is not in that list.
        """
        return None
