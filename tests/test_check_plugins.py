# SPDX-FileCopyrightText: 2020 - 2024 CERN
# SPDX-FileCopyrightText: 2023 - 2024 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

"""Test the `cernml.checkers` entry point."""

import typing as t
from unittest.mock import MagicMock, Mock, patch

import pytest

from cernml import coi


@pytest.fixture
def mock_entry_points() -> t.Iterator[MagicMock]:
    with patch(
        "cernml.coi.checkers._full_check.importlib_metadata.entry_points"
    ) as mock:
        yield mock


@pytest.fixture
def mock_check_problem() -> t.Iterator[MagicMock]:
    with patch("cernml.coi.checkers._full_check.check_problem") as mock:
        yield mock


def test_check_plugins(
    mock_entry_points: MagicMock,
    mock_check_problem: MagicMock,
) -> None:
    # Given:
    all_entry_points = mock_entry_points.return_value
    our_entry_points = all_entry_points.select.return_value = [Mock(), Mock()]
    problem = Mock(spec=coi.Problem)
    problem.unwrapped = problem
    headless = Mock()
    # When:
    coi.check(problem, warn=1, headless=headless)
    # Then:
    mock_check_problem.assert_called_once_with(problem, warn=3, headless=headless)
    mock_entry_points.assert_called_once_with()
    all_entry_points.select.assert_called_once_with(group="cernml.checkers")
    for entry_point in our_entry_points:
        entry_point.load.assert_called_once_with()
        checker = entry_point.load.return_value
        checker.assert_called_once_with(problem, warn=3, headless=headless)
