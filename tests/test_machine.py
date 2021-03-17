#!/usr/bin/env python
"""Test that `Machine` warns against using TitleCase names."""
# pylint: disable = missing-class-docstring, missing-function-docstring

import warnings

import pytest

from cernml import coi


@pytest.mark.parametrize("member", list(coi.Machine))
def test_names_are_all_upper(member: coi.Machine) -> None:
    assert member.name.isupper()


@pytest.mark.parametrize(
    "name, expected",
    [
        ("NoMachine", coi.Machine.NO_MACHINE),
        ("Linac2", coi.Machine.LINAC_2),
        ("Linac3", coi.Machine.LINAC_3),
        ("Linac4", coi.Machine.LINAC_4),
        ("Leir", coi.Machine.LEIR),
        ("Awake", coi.Machine.AWAKE),
    ],
)
def test_warn_against_legacy_names(name: str, expected: coi.Machine) -> None:
    with warnings.catch_warnings(record=True) as record:
        looked_up = coi.Machine[name]
    assert record, "no warning has been issued"
    [warning] = record
    assert warning.category is DeprecationWarning
    assert looked_up == expected


@pytest.mark.parametrize(
    "name", ["NoMachine", "Linac2", "Linac3", "Linac4", "Leir", "Awake"]
)
def test_getattr_getitem_consistent(name: str) -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        assert coi.Machine[name] is getattr(coi.Machine, name)
