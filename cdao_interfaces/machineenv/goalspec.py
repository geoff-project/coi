#!/usr/bin/env python
"""Provides the `GoalSpec` interface and examples of its implementation."""

from typing import Tuple

import numpy

Range = Tuple[float, float]


class GoalSpec:
    """A specification of the goal the `MachineEnv` has to reach.

    The `GoalSpec` provides one method, `evaluate()`, and one attribute,
    `reward_range`. The default reward range is always valid. While environment
    wrappers may make use of it, few practically do.
    """
    # pylint: disable=too-few-public-methods
    reward_range: Range = (-float('inf'), float('inf'))

    def evaluate_measurement(self, measurement,
                             info: dict) -> Tuple[float, bool]:
        """Evaluate the goodness of settings based on the given measurement.

        The results of the evaluation should be as close to physical values as
        possible. Any transformations to make the problem more amenable to
        reinforcement learning should be implemented via `gym.RewardWrapper`s.
        Examples include: reward normalization, limiting the number of steps
        per episode, giving a constant penaly per time step.

        Args:
            measurement: Return value of `Machine.take_measurement()`.
            info: A dictionary in which this method is free to insert useful
                meta information. For example, it is common to add
                `info['success']=True` if and only if the episode ended
                successfully.

        Returns:
            reward: A float that indicates how good the measurement is.
            done: A bool where True indicates that the episode should end and
                False that it should continue.
        """
        raise NotImplementedError()


class LambdaGoal(GoalSpec):
    """Decorator to turn free functions into `GoalSpec`s.

    Usage:
        >>> @LambdaGoal
        ... def neg_rms(deviation, info=None):
        ...     rms = numpy.sqrt(numpy.mean(numpy.square(deviation)))
        ...     if info is not None:
        ...         info['rms'] = rms
        ...     return -rms, False
        >>> neg_rms([1, 2, 2, 0])
        -1.5, False
        >>> info = {}
        >>> neg_rms.evaluate([1, 0, 2, 2], info)
        -1.5, False
        >>> info['rms']
        1.5

    Args:
        func: A callable with the same signature as `GoalSpec.evaluate()`. It
            will be called directly by `self.evaluate()`
        reward_range: If passed and not None, the reward range to use.
            Otherwise, the default range of `GoalSpec` is used.
    """
    def __init__(self, func, reward_range: Range = None):
        super().__init__()
        self.func = func
        if reward_range is not None:
            self.reward_range = reward_range

    def evaluate_measurement(self, measurement,
                             info: dict) -> Tuple[float, bool]:
        return self.func(measurement, info)

    __call__ = evaluate_measurement

    @classmethod
    def with_reward_range(cls, low: float, high: float):
        """Decorator that allows specifying the reward range.

        Usage:
            >>> @LambdaGoal.with_reward_range(-float('inf'), 0.0)
            ... def neg_rms(deviation, info=None):
            ...     rms = numpy.sqrt(numpy.mean(numpy.square(deviation)))
            ...     if info is not None:
            ...         info['rms'] = rms
            ...     return -rms, False
        """
        return lambda func: cls(func, reward_range=(low, high))


class BeamlineGoal(GoalSpec):
    """A `GoalSpec` suitable for beamline matching.

    This compares the measured beam trajectory to a reference trajectory. The
    reward is the negative RMS deviation. The episode ends if the beam either
    gets sufficiently close to the reference, or if it deviates too much from
    the center.

    Args:
        reference: The reference beam trajectory. It is given as an array of
            deviations from the beamline center, one element per beam-profile
            monitor in the line.
        goal_rms: The RMS below which the episode is considered successfully
            finished.
        max_deviation: If the absolute of any element of the trajectory exceeds
            this value, the episode is ended immediately. It represents the
            beam either hitting the beam line wall or coming too close to it.
    """

    # pylint: disable=too-few-public-methods

    def __init__(self, reference: numpy.ndarray, goal_rms: float,
                 max_deviation: float):
        super().__init__()
        assert goal_rms > 0.0
        assert max_deviation > 0.0
        self.reference = reference
        self.goal_rms = goal_rms
        self.max_deviation = max_deviation
        max_rms = _rms(max_deviation * numpy.ones_like(reference))
        self.reward_range = (-max_rms, 0.0)

    def evaluate_measurement(self, measurement, info):
        """Evaluate the given measurement and fill the `info` dict.

        Info entries:
            rms: The RMS deviation between the measured beam and the reference
                trajectory.
            success: Only added if the episode has ended. `True` if the beam
                got sufficiently close to the reference trajectory, `False` if
                it diverged too much from the center.
        """
        rms = numpy.sqrt(numpy.mean(numpy.square(measurement -
                                                 self.reference)))
        converged = rms < self.goal_rms
        diverged = any(abs(measurement) > self.max_deviation)
        reward = -rms
        done = not (converged or diverged)
        info['rms'] = rms
        if done:
            info['success'] = converged
        return reward, done


def _rms(array: numpy.ndarray) -> float:
    """Return the root-mean-square of an array."""
    return numpy.sqrt(numpy.mean(numpy.square(array)))
