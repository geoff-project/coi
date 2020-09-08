#!/usr/bin/env python
"""An environment interface that supports RL and numerical optimization."""

# pylint: disable = abstract-method, too-few-public-methods

from abc import ABCMeta, abstractmethod

import gym

__all__ = [
    'OptEnv',
    'OptGoalEnv',
    'Optimizable',
]


class Optimizable(metaclass=ABCMeta):
    """Additional mix-in for environments that are optimizable.

    Fundamentally, an environment contains a hidden state on which actions can
    performed. Each action causes a transition from one state to another. Each
    transition produces an observation and a reward.

    An environment is *optimizable* if additionally, there are certain
    *parameters* that can be set to transition to to a certain state. And each
    transition is associated with a *loss* that shall be minimized.

    The difference between actions and parameters is: actions describe a step
    that shall be taken in the phase space of states; parameters describe the
    point in phase space that shall be moved to. A parameter may be e.g. the
    electric current supplied to a magnet, and an action may be the value by
    which to increase or decrease that current.

    The difference between the parameters and the hidden state is that the
    parameters may describe only a *subset* of the state. There may be state
    variables that cannot be influenced by the optimizer.

    This mix-in does not provide any logic of its own. It merely defines a
    uniform interface through which a client may connect a numerical optimizer
    to a class that is normally used in reinforcement learning.

    Typically, you don't want to inherit from this mix-in directly. This
    package provides several classes that extend the `gym.Env` interface with
    it.

    Attributes:
        optimization_space: A `gym.Space` instance that describes the phase
            space of parameters. This may be the same or different from the
            `gym.Env.action_space`.
    """
    optimization_space = None

    @abstractmethod
    def compute_loss(self, parameters) -> float:
        """Perform an optimization step.

        This function is similar to `step()`, but it accepts parameters instead
        of an action. See the class docstring for the difference.

        This function may modify the environment, but it should fundamentally
        be stateless: Calling `compute_loss()` twice with the same parameters
        should return the same loss, excepting any stochastic noise.

        Args:
            parameters: The parameters for which the loss shall be calculated.
                This should be within `self.optimization_space`, but it must at
                least have the same structure.

        Returns:
            The loss associated with these parameters. Numerical optimizers may
            want to minimize that loss.
        """
        raise NotImplementedError()


class OptEnv(gym.Env, Optimizable):
    """An optimizable environment.

    This is an intersection of `Env` and `Optimizable`. See the respective
    abstract classes for their documentation.
    """


@OptEnv.register
class OptGoalEnv(gym.GoalEnv, Optimizable):
    """An optimizable multi-goal environment.

    This is an intersection of `GoalEnv` and `Optimizable`. See the respective
    abstract classes for their documentation.
    """
