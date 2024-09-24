# SPDX-FileCopyrightText: 2020 - 2024 CERN
# SPDX-FileCopyrightText: 2023 - 2024 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

"""Test global functions of the registration module."""

from __future__ import annotations

from inspect import signature
from unittest.mock import Mock

import gymnasium as gym
import pytest

from cernml import coi
from cernml.coi.registration import EnvRegistry


@pytest.fixture
def registry(monkeypatch: pytest.MonkeyPatch) -> Mock:
    mock = Mock(EnvRegistry, name="registry")
    mock.register.return_value = None
    monkeypatch.setattr("cernml.coi.registration._globals.registry", mock)
    return mock


def test_registry_class() -> None:
    assert isinstance(coi.registry, EnvRegistry)


def test_current_namespace(registry: Mock) -> None:
    assert coi.registration.current_namespace() == registry.current_namespace


def test_namespace(registry: Mock) -> None:
    ns = Mock(name="ns")
    res = coi.registration.namespace(ns)
    assert res == registry.namespace.return_value
    registry.namespace.assert_called_once_with(ns)


def test_pprint_registry(registry: Mock) -> None:
    # Given:
    sig = signature(gym.envs.registration.pprint_registry)
    kwargs = {
        p.name: p.default for p in sig.parameters.values() if p.kind == p.KEYWORD_ONLY
    }
    # When:
    res = coi.pprint_registry()
    # Then:
    assert res == registry.pprint.return_value
    registry.pprint.assert_called_once_with(**kwargs)


@pytest.mark.parametrize("funcname", ["register", "make", "spec", "make_vec"])
def test_forwarding(registry: Mock, funcname: str) -> None:
    # Given:
    sig = signature(getattr(gym, funcname))
    kwargs = {
        p.name: p.default for p in sig.parameters.values() if p.default is not p.empty
    }
    if funcname != "spec":
        # Set by `bump_stacklevel`.
        kwargs["stacklevel"] = 3
    if funcname == "make":
        # Documented as deviation from gymnasium.make().
        kwargs["order_enforce"] = None
    func = getattr(coi, funcname)
    target: Mock = getattr(registry, funcname)
    arg = Mock(name="arg")
    # When:
    res = func(arg)
    # Then:
    assert res == target.return_value
    target.assert_called_once_with(arg, **kwargs)
