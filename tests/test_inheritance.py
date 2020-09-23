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


def _assert_env_subclass(subclass, superclasses):
    all_superclasses = (
        gym.GoalEnv,
        coi.SingleOptimizable,
        coi.OptEnv,
        coi.OptGoalEnv,
        coi.SeparableEnv,
        coi.SeparableOptEnv,
        coi.SeparableGoalEnv,
        coi.SeparableOptGoalEnv,
    )
    for superclass in all_superclasses:
        assert (superclass in superclasses) == issubclass(subclass, superclass)


def _is_abstract_base_class(abc, superclasses):
    class NoDirectInheritance(*superclasses):
        # pylint: disable = too-few-public-methods
        pass

    return issubclass(NoDirectInheritance, abc)


def test_env_problem():
    assert issubclass(gym.Env, coi.Problem)


def test_optenv_is_abstract():
    assert _is_abstract_base_class(coi.OptEnv,
                                   [gym.Env, coi.SingleOptimizable])


def test_optgoalenv_is_abstract():
    assert _is_abstract_base_class(
        coi.OptGoalEnv,
        [gym.GoalEnv, coi.SingleOptimizable],
    )


def test_sepoptenv_is_abstract():
    assert _is_abstract_base_class(
        coi.SeparableOptEnv,
        [coi.SeparableEnv, coi.SingleOptimizable],
    )


def test_sepoptgoalenv_is_abstract():
    assert _is_abstract_base_class(
        coi.SeparableOptGoalEnv,
        [coi.SeparableGoalEnv, coi.SingleOptimizable],
    )


def test_env():
    _assert_env_subclass(ConcreteEnv, [gym.Env])


def test_optenv():
    _assert_env_subclass(
        ConcreteOptEnv,
        [gym.Env, coi.SingleOptimizable, coi.OptEnv],
    )


def test_goalenv():
    _assert_env_subclass(ConcreteGoalEnv, [gym.Env, gym.GoalEnv])


def test_optgoalenv():
    _assert_env_subclass(
        ConcreteOptGoalEnv,
        [
            gym.Env, gym.GoalEnv, coi.SingleOptimizable, coi.OptEnv,
            coi.OptGoalEnv
        ],
    )


def test_sepenv():
    _assert_env_subclass(
        ConcreteSeparableEnv,
        [gym.Env, coi.SeparableEnv],
    )


def test_sepoptenv():
    _assert_env_subclass(
        ConcreteSeparableOptEnv,
        [
            gym.Env,
            coi.SingleOptimizable,
            coi.OptEnv,
            coi.SeparableEnv,
            coi.SeparableOptEnv,
        ],
    )


def test_sepgoalenv():
    # SeparableGoalEnv is not a SeparableEnv. Their compute_reward() methods
    # are semantically different.
    _assert_env_subclass(
        ConcreteSeparableGoalEnv,
        [gym.Env, gym.GoalEnv, coi.SeparableGoalEnv],
    )


def test_sepoptgoalenv():
    # SeparableOptGoalEnv is not a SeparableEnv. Their compute_reward() methods
    # are semantically different.
    _assert_env_subclass(
        ConcreteSeparableOptGoalEnv,
        [
            gym.Env,
            gym.GoalEnv,
            coi.SingleOptimizable,
            coi.OptEnv,
            coi.OptGoalEnv,
            coi.SeparableGoalEnv,
            coi.SeparableOptGoalEnv,
        ],
    )
