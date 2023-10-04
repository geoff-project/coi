# SPDX-FileCopyrightText: 2020-2024 CERN
# SPDX-FileCopyrightText: 2023-2024 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

"""Test the registration module."""

import typing
from unittest.mock import Mock, patch

import pytest

from cernml import coi


@pytest.fixture
def mock_registry() -> typing.Iterator[Mock]:
    with patch("cernml.coi._registration.registry") as mock:
        yield mock


def test_register(mock_registry: Mock) -> None:
    env_name = Mock()
    entry_point = Mock()
    nondeterministic = Mock()
    max_episode_steps = Mock()
    order_enforce = Mock()
    kwargs = Mock()
    coi.register(
        env_name,
        entry_point=entry_point,
        nondeterministic=nondeterministic,
        max_episode_steps=max_episode_steps,
        order_enforce=order_enforce,
        kwargs=kwargs,
    )
    mock_registry.register.assert_called_once_with(
        env_name,
        entry_point=entry_point,
        nondeterministic=nondeterministic,
        max_episode_steps=max_episode_steps,
        order_enforce=order_enforce,
        kwargs=kwargs,
    )


def test_make(mock_registry: Mock) -> None:
    env_name = Mock()
    kwargs = {"foo": Mock(), "bar": Mock()}
    res = coi.make(env_name, **kwargs)
    mock_registry.make.assert_called_once_with(env_name, **kwargs)
    assert res is mock_registry.make.return_value


def test_spec(mock_registry: Mock) -> None:
    env_name = Mock()
    res = coi.spec(env_name)
    mock_registry.spec.assert_called_once_with(env_name)
    assert res is mock_registry.spec.return_value
