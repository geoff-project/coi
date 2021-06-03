"""Test the registration module."""

# pylint: disable = missing-class-docstring
# pylint: disable = missing-function-docstring
# pylint: disable = redefined-outer-name

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
    kwargs = Mock()
    coi.register(
        env_name,
        entry_point=entry_point,
        nondeterministic=nondeterministic,
        max_episode_steps=max_episode_steps,
        kwargs=kwargs,
    )
    mock_registry.register.assert_called_once_with(
        env_name,
        entry_point=entry_point,
        nondeterministic=nondeterministic,
        max_episode_steps=max_episode_steps,
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
