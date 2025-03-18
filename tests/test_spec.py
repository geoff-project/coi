# SPDX-FileCopyrightText: 2020 - 2025 CERN
# SPDX-FileCopyrightText: 2023 - 2025 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

"""Test our implementation of `EnvSpec`."""

from __future__ import annotations

import typing as t
from unittest.mock import Mock

import pytest
from gymnasium import Env

from cernml.coi.registration._base import EnvSpec as GymEnvSpec
from cernml.coi.registration._base import WrapperSpec
from cernml.coi.registration._spec import (
    EnvSpec,
    MinimalEnvSpec,
    bump_stacklevel,
    downcast_spec,
)


def test_bump_stacklevel() -> None:
    kwargs: dict[str, int] = {}
    assert bump_stacklevel(kwargs) == 2
    assert kwargs["stacklevel"] == 3
    kwargs = {"stacklevel": 0}
    assert bump_stacklevel(kwargs) == 0
    assert kwargs["stacklevel"] == 1
    kwargs = {"stacklevel": 1}
    assert bump_stacklevel(kwargs) == 1
    assert kwargs["stacklevel"] == 2


def test_minimal_env_spec() -> None:
    """No-op test, only used for type checking."""

    def _take_proto(_: MinimalEnvSpec) -> None:
        pass

    _take_proto(t.cast(EnvSpec, None))
    _take_proto(t.cast(GymEnvSpec, None))


def test_inheritance() -> None:
    assert issubclass(GymEnvSpec, EnvSpec)


def test_env_spec_attributes() -> None:
    expected_diff = {
        "__abstractmethods__",  # Added by `abc`.
        "_abc_impl",  # Added by `abc`.
        "__slotnames__",  # Added by `copyreg`, via `copy.deepcopy()`.
    }
    assert set(dir(EnvSpec)) - expected_diff == set(dir(GymEnvSpec))
    assert vars(EnvSpec).keys() - expected_diff == vars(GymEnvSpec).keys()


def test_env_spec_parse() -> None:
    spec = EnvSpec("ns/name-v1")
    assert spec.namespace == "ns"
    assert spec.name == "name"
    assert spec.version == 1


def test_env_spec_make(monkeypatch: pytest.MonkeyPatch) -> None:
    make = Mock(name="make")
    arg = Mock(name="arg")
    monkeypatch.setattr("cernml.coi.registration._make.make", make)
    spec = EnvSpec("ns/name-v1")
    result = spec.make(arg=arg, stacklevel=42)
    assert result == make.return_value
    make.assert_called_once_with(spec, arg=arg, stacklevel=43)


def test_env_spec_json() -> None:
    expected = EnvSpec(
        id="ns/name-v1",
        entry_point="",
        additional_wrappers=(WrapperSpec(name="wrapper", entry_point="", kwargs={}),),
    )
    json = expected.to_json()
    actual = EnvSpec.from_json(json)
    assert isinstance(actual, EnvSpec)
    assert expected == actual


def test_env_spec_json_failures() -> None:
    def entry_point(**kwargs: t.Any) -> Env:
        raise NotImplementedError

    expected = EnvSpec(id="ns/name-v1", entry_point=entry_point)
    with pytest.raises(ValueError, match="serialization of callables"):
        expected.to_json()
    with pytest.raises(ValueError, match="EnvSpec from JSON:"):
        EnvSpec.from_json('{"id": "ns/name-v1", "badarg": null}')
    with pytest.raises(ValueError, match="WrapperSpec from JSON:"):
        EnvSpec.from_json('{"id": "ns/name-v1", "additional_wrappers": [{}]}')


def test_downcast() -> None:
    spec = EnvSpec("ns/name-v1")
    assert isinstance(spec, EnvSpec)
    assert not isinstance(spec, GymEnvSpec)
    result = downcast_spec(spec)
    assert isinstance(result, EnvSpec)
    assert isinstance(result, GymEnvSpec)


def test_downcast_idempotent() -> None:
    spec = downcast_spec(EnvSpec("ns/name-v1"))
    assert isinstance(spec, EnvSpec)
    assert downcast_spec(spec) is spec
