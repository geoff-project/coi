"""Test the `cernml.coi.checkers` entry poiny."""

# pylint: disable = missing-class-docstring
# pylint: disable = missing-function-docstring
# pylint: disable = redefined-outer-name

import typing as t
from unittest.mock import MagicMock, Mock, patch

import pytest

from cernml import coi


@pytest.fixture
def mock_entry_points() -> t.Iterator[MagicMock]:
    with patch("importlib_metadata.entry_points") as mock:
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
    warn = Mock()
    headless = Mock()
    # When:
    coi.check(problem, warn=warn, headless=headless)
    # Then:
    mock_check_problem.assert_called_once_with(problem, warn=warn, headless=headless)
    mock_entry_points.assert_called_once_with()
    all_entry_points.select.assert_called_once_with(group="cernml.coi.checkers")
    for entry_point in our_entry_points:
        entry_point.load.assert_called_once_with()
        checker = entry_point.load.return_value
        checker.assert_called_once_with(problem, warn=warn, headless=headless)
