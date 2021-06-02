"""Test that `Machine` warns against using TitleCase names."""
# pylint: disable = missing-class-docstring, missing-function-docstring

import pytest

from cernml import coi


@pytest.mark.parametrize("member", list(coi.Machine))
def test_names_are_all_upper(member: coi.Machine) -> None:
    assert member.name.isupper()


@pytest.mark.parametrize(
    "name", ["NoMachine", "Linac2", "Linac3", "Linac4", "Leir", "Awake"]
)
def test_error_on_legacy_names(name: str) -> None:
    with pytest.raises(KeyError, match=name):
        _ = coi.Machine[name]
