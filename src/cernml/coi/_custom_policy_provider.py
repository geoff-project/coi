# SPDX-FileCopyrightText: 2020-2024 CERN
# SPDX-FileCopyrightText: 2023-2024 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

"""Definition of the `CustomPolicyProvider` interface."""

from __future__ import annotations

import typing as t
from abc import ABCMeta, abstractmethod

import numpy as np

from ._abc_helpers import check_class_methods, check_methods


class Policy(metaclass=ABCMeta):
    """Interface of RL algorithms returned by `CustomPolicyProvider`.

    This is an :term:`std:abstract base class`. This means even classes
    that don't inherit from it may be considered a subclass. To be
    considered a subclass, a class must merely provide a method called
    `predict()`. The signature of this method has been chosen to be
    compatible with :doc:`Stable Baselines <sb3:index>`.

    .. warning::
        When implementing this method yourself, be careful to return
        a :samp:`({action}, {state})` tuple! If your policy is
        non-recursive, the *state* should be simply None.
    """

    @abstractmethod
    def predict(
        self,
        observation: t.Union[np.ndarray, t.Dict[str, np.ndarray]],
        state: t.Optional[t.Tuple[np.ndarray, ...]] = None,
        episode_start: t.Optional[np.ndarray] = None,
        deterministic: bool = False,
    ) -> t.Tuple[np.ndarray, t.Optional[t.Tuple[np.ndarray, ...]]]:
        """Get the policy action from an observation (and hidden state).

        Args:
            observation: the input observation.
            state: The last hidden states. On the first call and when
                using non-recurrent policies, this should be None (the
                default).
            episode_start: The last masks. For non-recurrent policies,
                this is just None (the default). For recurrent policies,
                this is an array of the same length as *state*. That
                could be e.g. the number of parallel vector
                environments. An entry should be 1 if the internal state
                should reset on, 0 otherwise. This means that on the
                first call (when *state* is necesarily None), this
                should be an array of only ones.
            deterministic: If True, return deterministic actions. If
                False (the default), return stochastic actions, e.g. by
                enabling action noise.

        Returns:
            The chosen action and, if this is a recurrent policy, the
            next hidden state. Non-recurrent policies always return None
            as a state.
        """

    @classmethod
    def __subclasshook__(cls, other: type) -> t.Any:
        if cls is Policy:
            return check_methods(other, "predict")
        return NotImplemented


class CustomPolicyProvider(metaclass=ABCMeta):
    """Interface for optimization problems with custom RL algorithms.

    This protocol gives subclasses of `~gym.Env` the opportunity to
    dynamically collect and return RL agents that are tailored to the
    problem. Host applications are expected to check the presence of
    this interface and, if possible, call `get_policy_names()` before
    presenting a list of agents to the user.

    The interface is split into two parts:

    1. `get_policy_names()` collects the list of available agents or
       policies and returns a list of names.

    2. `load_policy()` receives the name of the chosen agent or policy
       should load it.

    The object returned by `load_policy()` is expected to have a method
    `~Policy.predict()`. All algorithms and policy classes of
    :doc:`Stable Baselines <sb3:index>` satisfy this interface.

    This is an :term:`std:abstract base class`. This means even classes
    that don't inherit from it may be considered a subclass. To be
    considered a subclass, a class must merely provide
    a `std:classmethod` with the name ``get_policy_names`` and
    a *regular* method with the name ``load_policy``.

    Custom policies may also be provided through an :doc:`entry point
    <pkg:specifications/entry-points>`. Entry points in the group
    ``cernml.custom_policies`` that have the same name as the
    *registered* name of the environment (not the class name!) must
    point to a subclass of `CustomPolicyProvider`. The class must be
    instantiable by calling it without arguments. A host application may
    load and invoke such an entry point if and only if the user selects
    an optimization problem with a matching name.
    """

    @classmethod
    @abstractmethod
    def get_policy_names(cls) -> t.List[str]:
        """Return a list of all available policies.

        How this list is acquired is left to the implementation.
        Possible choices are to hard-code it, to glob a local directory
        for stored weights, or to request a list from the Internet.

        Each policy name should be unique and readable by a human user.

        The default implementation returns an empty list.
        """
        return []

    @abstractmethod
    def load_policy(self, name: str) -> Policy:
        """Load the chosen policy.

        How this is done is left to the implementation. Typically, this
        involves instantiating an algorithm class and loading
        pre-trained weights into it.
        """
        raise NotImplementedError

    @classmethod
    def __subclasshook__(cls, other: type) -> t.Any:
        if cls is CustomPolicyProvider:
            # Mind the return value, it could be `NotImplemented`!
            class_match = check_class_methods(other, "get_policy_names")
            if class_match is not True:
                return class_match
            return check_methods(other, "load_policy")
        return NotImplemented
