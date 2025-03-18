# SPDX-FileCopyrightText: 2020 - 2025 CERN
# SPDX-FileCopyrightText: 2023 - 2025 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

# pylint: disable = missing-class-docstring
# pylint: disable = missing-function-docstring
# pylint: disable = redefined-outer-name

"""Test that `Machine` warns against using TitleCase names."""

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
