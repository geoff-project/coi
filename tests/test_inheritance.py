#!/usr/bin/env python
"""Test the inheritance chain of the package."""

# pylint: disable = missing-class-docstring, missing-function-docstring
# pylint: disable = abstract-method

import gym

from cernml import coi


class ConcreteEnv(gym.Env):
    pass


class ConcreteOptEnv(coi.OptEnv):
    pass


class ConcreteGoalEnv(gym.GoalEnv):
    pass


class ConcreteOptGoalEnv(coi.OptGoalEnv):
    pass


class ConcreteSeparableEnv(coi.SeparableEnv):
    pass


class ConcreteSeparableOptEnv(coi.SeparableOptEnv):
    pass


class ConcreteSeparableGoalEnv(coi.SeparableGoalEnv):
    pass


class ConcreteSeparableOptGoalEnv(coi.SeparableOptGoalEnv):
    pass


def test_env_problem():
    assert issubclass(gym.Env, coi.Problem)


def test_env():
    assert issubclass(ConcreteEnv, gym.Env)
    assert not issubclass(ConcreteEnv, gym.GoalEnv)
    assert not issubclass(ConcreteEnv, coi.Optimizable)
    assert not issubclass(ConcreteEnv, coi.OptEnv)
    assert not issubclass(ConcreteEnv, coi.OptGoalEnv)
    assert not issubclass(ConcreteEnv, coi.SeparableEnv)
    assert not issubclass(ConcreteEnv, coi.SeparableOptEnv)
    assert not issubclass(ConcreteEnv, coi.SeparableGoalEnv)
    assert not issubclass(ConcreteEnv, coi.SeparableOptGoalEnv)


def test_goalenv():
    assert issubclass(ConcreteOptEnv, gym.Env)
    assert not issubclass(ConcreteOptEnv, gym.GoalEnv)
    assert issubclass(ConcreteOptEnv, coi.Optimizable)
    assert issubclass(ConcreteOptEnv, coi.OptEnv)
    assert not issubclass(ConcreteOptEnv, coi.OptGoalEnv)
    assert not issubclass(ConcreteOptEnv, coi.SeparableEnv)
    assert not issubclass(ConcreteOptEnv, coi.SeparableOptEnv)
    assert not issubclass(ConcreteOptEnv, coi.SeparableGoalEnv)
    assert not issubclass(ConcreteOptEnv, coi.SeparableOptGoalEnv)


def test_goal_env():
    assert issubclass(ConcreteGoalEnv, gym.Env)
    assert issubclass(ConcreteGoalEnv, gym.GoalEnv)
    assert not issubclass(ConcreteGoalEnv, coi.Optimizable)
    assert not issubclass(ConcreteGoalEnv, coi.OptEnv)
    assert not issubclass(ConcreteGoalEnv, coi.OptGoalEnv)
    assert not issubclass(ConcreteGoalEnv, coi.SeparableEnv)
    assert not issubclass(ConcreteGoalEnv, coi.SeparableOptEnv)
    assert not issubclass(ConcreteGoalEnv, coi.SeparableGoalEnv)
    assert not issubclass(ConcreteGoalEnv, coi.SeparableOptGoalEnv)


def test_optgoalenv():
    assert issubclass(ConcreteOptGoalEnv, gym.Env)
    assert issubclass(ConcreteOptGoalEnv, gym.GoalEnv)
    assert issubclass(ConcreteOptGoalEnv, coi.Optimizable)
    assert issubclass(ConcreteOptGoalEnv, coi.OptEnv)
    assert issubclass(ConcreteOptGoalEnv, coi.OptGoalEnv)
    assert not issubclass(ConcreteOptGoalEnv, coi.SeparableEnv)
    assert not issubclass(ConcreteOptGoalEnv, coi.SeparableOptEnv)
    assert not issubclass(ConcreteOptGoalEnv, coi.SeparableGoalEnv)
    assert not issubclass(ConcreteOptGoalEnv, coi.SeparableOptGoalEnv)


def test_sepenv():
    assert issubclass(ConcreteSeparableEnv, gym.Env)
    assert not issubclass(ConcreteSeparableEnv, gym.GoalEnv)
    assert not issubclass(ConcreteSeparableEnv, coi.Optimizable)
    assert not issubclass(ConcreteSeparableEnv, coi.OptEnv)
    assert not issubclass(ConcreteSeparableEnv, coi.OptGoalEnv)
    assert issubclass(ConcreteSeparableEnv, coi.SeparableEnv)
    assert not issubclass(ConcreteSeparableEnv, coi.SeparableOptEnv)
    assert not issubclass(ConcreteSeparableEnv, coi.SeparableGoalEnv)
    assert not issubclass(ConcreteSeparableEnv, coi.SeparableOptGoalEnv)


def test_sepoptenv():
    assert issubclass(ConcreteSeparableOptEnv, gym.Env)
    assert not issubclass(ConcreteSeparableOptEnv, gym.GoalEnv)
    assert issubclass(ConcreteSeparableOptEnv, coi.Optimizable)
    assert issubclass(ConcreteSeparableOptEnv, coi.OptEnv)
    assert not issubclass(ConcreteSeparableOptEnv, coi.OptGoalEnv)
    assert issubclass(ConcreteSeparableOptEnv, coi.SeparableEnv)
    assert issubclass(ConcreteSeparableOptEnv, coi.SeparableOptEnv)
    assert not issubclass(ConcreteSeparableOptEnv, coi.SeparableGoalEnv)
    assert not issubclass(ConcreteSeparableOptEnv, coi.SeparableOptGoalEnv)


def test_sepgoalenv():
    assert issubclass(ConcreteSeparableGoalEnv, gym.Env)
    assert issubclass(ConcreteSeparableGoalEnv, gym.GoalEnv)
    assert not issubclass(ConcreteSeparableGoalEnv, coi.Optimizable)
    assert not issubclass(ConcreteSeparableGoalEnv, coi.OptEnv)
    assert not issubclass(ConcreteSeparableGoalEnv, coi.OptGoalEnv)
    # SeparableGoalEnv is not a SeparableEnv. Their compute_reward() methods
    # are semantically different.
    assert not issubclass(ConcreteSeparableGoalEnv, coi.SeparableEnv)
    assert issubclass(ConcreteSeparableGoalEnv, coi.SeparableGoalEnv)
    assert not issubclass(ConcreteSeparableGoalEnv, coi.SeparableOptEnv)
    assert not issubclass(ConcreteSeparableGoalEnv, coi.SeparableOptGoalEnv)


def test_sepoptgoalenv():
    assert issubclass(ConcreteSeparableOptGoalEnv, gym.Env)
    assert issubclass(ConcreteSeparableOptGoalEnv, gym.GoalEnv)
    assert issubclass(ConcreteSeparableOptGoalEnv, coi.Optimizable)
    assert issubclass(ConcreteSeparableOptGoalEnv, coi.OptEnv)
    assert issubclass(ConcreteSeparableOptGoalEnv, coi.OptGoalEnv)
    # SeparableGoalEnv is not a SeparableEnv. Their compute_reward() methods
    # are semantically different.
    assert not issubclass(ConcreteSeparableOptGoalEnv, coi.SeparableEnv)
    assert not issubclass(ConcreteSeparableOptGoalEnv, coi.SeparableOptEnv)
    assert issubclass(ConcreteSeparableOptGoalEnv, coi.SeparableGoalEnv)
    assert issubclass(ConcreteSeparableOptGoalEnv, coi.SeparableOptGoalEnv)
