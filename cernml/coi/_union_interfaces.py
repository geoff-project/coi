"""Interfaces that combine two or more base interfaces."""

from abc import ABCMeta
from typing import Any

import gym

from ._optenv import SingleOptimizable
from ._sepenv import SeparableEnv, SeparableGoalEnv


class OptEnv(gym.Env, SingleOptimizable, metaclass=ABCMeta):
    """An optimizable environment.

    This is an intersection of :class:`~gym.Env` and
    :class:`SingleOptimizable`. Any class that inherits from both, also
    inherits from this class.
    """

    @classmethod
    def __subclasshook__(cls, other: type) -> Any:
        if cls is OptEnv:
            bases = other.__mro__
            return gym.Env in bases and SingleOptimizable in bases
        return NotImplemented


class OptGoalEnv(gym.GoalEnv, SingleOptimizable, metaclass=ABCMeta):
    """An optimizable multi-goal environment.

    This is an intersection of :class:`~gym.GoalEnv` and
    :class:`SingleOptimizable`. Any class that inherits from both, also
    inherits from this class.
    """

    @classmethod
    def __subclasshook__(cls, other: type) -> Any:
        if cls is OptGoalEnv:
            bases = other.__mro__
            return gym.GoalEnv in bases and SingleOptimizable in bases
        return NotImplemented


class SeparableOptEnv(SeparableEnv, SingleOptimizable, metaclass=ABCMeta):
    """An optimizable and separable environment.

    This is an intersection of :class:`SeparableEnv` and
    :class:`SingleOptimizable`. Any class that inherits from both, also
    inherits from this class.
    """

    @classmethod
    def __subclasshook__(cls, other: type) -> Any:
        if cls is SeparableOptEnv:
            bases = other.__mro__
            return SeparableEnv in bases and SingleOptimizable in bases
        return NotImplemented


class SeparableOptGoalEnv(SeparableGoalEnv, SingleOptimizable, metaclass=ABCMeta):
    """An optimizable and separable multi-goal environment.

    This is an intersection of :class:`SeparableGoalEnv` and
    :class:`SingleOptimizable`. Any class that inherits from both, also
    inherits from this class.
    """

    @classmethod
    def __subclasshook__(cls, other: type) -> Any:
        if cls is SeparableOptGoalEnv:
            bases = other.__mro__
            return SeparableGoalEnv in bases and SingleOptimizable in bases
        return NotImplemented
