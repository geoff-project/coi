# SPDX-FileCopyrightText: 2020-2024 CERN
# SPDX-FileCopyrightText: 2023-2024 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

"""Test the inheritance behavior of `CustomOptimizerProvider`."""

import typing as t

import numpy as np
import pytest

from cernml import coi


class DirectPolicy(coi.Policy):
    # pylint: disable = too-few-public-methods
    def __init__(self, name: str) -> None:
        self.name = name

    def predict(
        self,
        observation: t.Union[np.ndarray, t.Dict[str, np.ndarray]],
        state: t.Optional[t.Tuple[np.ndarray, ...]] = None,
        episode_start: t.Optional[np.ndarray] = None,
        deterministic: bool = False,
    ) -> t.Tuple[np.ndarray, t.Optional[t.Tuple[np.ndarray, ...]]]:
        return np.zeros(3), None


class DirectProvider(coi.CustomPolicyProvider):
    # pylint: disable = too-few-public-methods
    @classmethod
    def get_policy_names(cls) -> t.List[str]:
        return super().get_policy_names() + ["name"]

    def load_policy(self, name: str) -> coi.Policy:
        return DirectPolicy(name)


class IndirectPolicy:
    # pylint: disable = too-few-public-methods
    def __init__(self, name: str) -> None:
        self.name = name

    def predict(
        self,
        observation: t.Union[np.ndarray, t.Dict[str, np.ndarray]],
        state: t.Optional[t.Tuple[np.ndarray, ...]] = None,
        episode_start: t.Optional[np.ndarray] = None,
        deterministic: bool = False,
    ) -> t.Tuple[np.ndarray, t.Optional[t.Tuple[np.ndarray, ...]]]:
        # pylint: disable = unused-argument
        return np.zeros(3), None


class IndirectProvider:
    # pylint: disable = too-few-public-methods
    @classmethod
    def get_policy_names(cls) -> t.List[str]:
        return ["name"]

    def load_policy(self, name: str) -> IndirectPolicy:
        return IndirectPolicy(name)


@pytest.mark.parametrize("subclass", [DirectProvider, IndirectProvider])
def test_custom_optimizer_provider_defaults(
    subclass: t.Type[coi.CustomOptimizerProvider],
) -> None:
    env = subclass()
    # pylint: disable = assignment-from-none
    # pylint: disable = use-implicit-booleaness-not-comparison
    assert isinstance(env, coi.CustomPolicyProvider)
    assert env.get_policy_names() == ["name"]
    assert isinstance(env.load_policy("name"), coi.Policy)


def test_negative() -> None:
    assert not isinstance(object(), coi.CustomPolicyProvider)
    assert not isinstance(object(), coi.Policy)
