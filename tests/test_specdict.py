# SPDX-FileCopyrightText: 2020-2024 CERN
# SPDX-FileCopyrightText: 2023-2024 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

"""Test the `SpecDict` helper type for `EnvRegistry`."""

from __future__ import annotations

import typing as t

import pytest

from cernml.coi.registration import EnvSpec, errors
from cernml.coi.registration._specdict import (
    EnvSpecDict,
    EnvSpecMapping,
    raise_env_not_found,
)


@pytest.fixture
def the_dict() -> EnvSpecDict:
    res = EnvSpecDict()
    for name in [
        "ns/name",
        "ns/name-v1",
        "ns/name-v2",
        "ns/noversion",
        "nonamespace-v1",
    ]:
        res[name] = EnvSpec(name, "")
    return res


def test_covariance() -> None:
    """No-op test, only used for MyPy."""

    def _takes_mapping(d: EnvSpecMapping) -> EnvSpecMapping:
        return d

    i = EnvSpecDict()
    o = _takes_mapping(i)
    assert isinstance(i, EnvSpecMapping)
    assert isinstance(o, EnvSpecMapping)
    assert isinstance(i, EnvSpecDict)
    assert isinstance(o, EnvSpecDict)
    assert i is o


def test_select_nothing(the_dict: EnvSpecDict) -> None:
    assert list(the_dict.select()) == list(the_dict.values())


def test_select_namespace(the_dict: EnvSpecDict) -> None:
    assert [spec.id for spec in the_dict.select(ns=None)] == [
        "nonamespace-v1",
    ]
    assert [spec.id for spec in the_dict.select(ns="ns")] == [
        "ns/name",
        "ns/name-v1",
        "ns/name-v2",
        "ns/noversion",
    ]
    assert not list(the_dict.select(ns=t.cast(t.Any, True)))


def test_select_version(the_dict: EnvSpecDict) -> None:
    assert list(the_dict.select()) == list(the_dict.values())
    assert [spec.id for spec in the_dict.select(version=True)] == [
        "ns/name-v1",
        "ns/name-v2",
        "nonamespace-v1",
    ]
    assert [spec.id for spec in the_dict.select(version=None)] == [
        "ns/name",
        "ns/noversion",
    ]
    assert [spec.id for spec in the_dict.select(version=1)] == [
        "ns/name-v1",
        "nonamespace-v1",
    ]


def test_select_name(the_dict: EnvSpecDict) -> None:
    assert [spec.id for spec in the_dict.select(name="name")] == [
        "ns/name",
        "ns/name-v1",
        "ns/name-v2",
    ]
    assert [spec.id for spec in the_dict.select(name="noversion")] == [
        "ns/noversion",
    ]
    assert not list(the_dict.select(name=t.cast(t.Any, None)))


@pytest.mark.parametrize(
    ("env_id", "exc_type", "match"),
    [
        ("n-s/name-v1", errors.NamespaceNotFoundError, "Did you mean: `ns`\\?$"),
        ("other/name-v1", errors.NamespaceNotFoundError, "Have you installed"),
        (
            "ns/named-v1",
            errors.NameNotFoundError,
            "exist in n\\w+e ns. Did you mean: `name`\\?$",
        ),
        ("badname", errors.NameNotFoundError, "doesn't exist.$"),
        (
            "nonamespace-v2",
            errors.VersionNotFoundError,
            "`v2` for environment `nonamespace` doesn't exist. "
            "It provides versioned environments: \\[ `v1` \\].$",
        ),
        (
            "nonamespace",
            errors.VersionNotFoundError,
            "Unversioned environment `nonamespace` doesn't exist. "
            "It provides versioned environments: \\[ `v1` \\].$",
        ),
        (
            "ns/noversion-v1",
            errors.DeprecatedEnv,
            "`v1` for environment `ns/noversion` doesn't exist. "
            "It provides the default version `ns/noversion`.$",
        ),
        (
            "ns/name-v0",
            errors.DeprecatedEnv,
            "`v0` for environment `ns/name` doesn't exist. "
            "It provides the default version `ns/name`. "
            "Please use `ns/name-v2` instead.$",
        ),
    ],
)
def test_error_messages(
    env_id: str, exc_type: type[Exception], match: str, the_dict: EnvSpecDict
) -> None:
    spec = EnvSpec(env_id, "")
    with pytest.raises(exc_type, match=match):
        raise_env_not_found(spec, the_dict)
