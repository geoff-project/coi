# SPDX-FileCopyrightText: 2020 - 2025 CERN
# SPDX-FileCopyrightText: 2023 - 2025 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

"""Test the `Plugins` helper type for `EnvRegistry`."""

from __future__ import annotations

from unittest.mock import MagicMock, call

import pytest

from cernml.coi.registration._plugins import Plugins
from cernml.coi.registration.errors import PluginWarning


@pytest.fixture(autouse=True)
def importlib(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    module = MagicMock(name="importlib_metadata")
    monkeypatch.setattr("cernml.coi.registration._plugins.importlib_metadata", module)
    return module


@pytest.fixture
def entry_points(importlib: MagicMock) -> MagicMock:
    entry_points = importlib.EntryPoints.return_value
    entry_points.names = [MagicMock(name=f"plugin_name_{i}") for i in range(1, 4)]
    return entry_points


def test_no_group(importlib: MagicMock) -> None:
    plugins = Plugins(group=None)
    assert not plugins.unloaded
    importlib.EntryPoints.assert_called_once_with()


def test_group(importlib: MagicMock) -> None:
    group = MagicMock(name="group")
    plugins = Plugins(group)
    assert plugins.entry_points == importlib.entry_points.return_value
    importlib.entry_points.assert_called_once_with(group=group)


def test_unloaded(entry_points: MagicMock) -> None:
    plugins = Plugins(group=None)
    assert plugins.unloaded == set(entry_points.names)
    assert entry_points.select.call_args_list == [
        call(name=name) for name in entry_points.names
    ]
    assert str(plugins) == "<plugins in 3 namespaces (loaded: [])>"


def test_load_empty_ns() -> None:
    name = MagicMock(name="name")
    plugins = Plugins(group=None)
    plugins.load(name)
    assert not plugins.loaded


def test_load(entry_points: MagicMock) -> None:
    # Given:
    plugin = MagicMock(name="plugin")
    entry_points.select.return_value = [plugin]
    name = entry_points.names[0]
    # When:
    plugins = Plugins(group=None)
    assert plugins.unloaded == set(entry_points.names)
    plugins.load(name)
    # Then:
    assert plugins.loaded == {name}
    assert plugins.unloaded == set(entry_points.names[1:])
    plugin.load.assert_called_once_with()
    plugin.load.return_value.assert_called_once_with()


def test_load_fails(entry_points: MagicMock) -> None:
    # Given:
    plugin = MagicMock(name="plugin")
    plugin.load.side_effect = ValueError
    entry_points.select.return_value = [plugin]
    # When:
    plugins = Plugins(group=None)
    # Then:
    with pytest.warns(PluginWarning, match="ValueError"):
        plugins.load(entry_points.names[0])


def test_load_problem(entry_points: MagicMock, monkeypatch: pytest.MonkeyPatch) -> None:
    # Given:
    plugin = MagicMock(name="plugin")
    entry_points.select.return_value = [plugin]
    is_problem_class = MagicMock(name="is_problem_class")
    monkeypatch.setattr("cernml.coi._typeguards.is_problem_class", is_problem_class)
    # When:
    plugins = Plugins(group=None)
    plugins.load(entry_points.names[0])
    # Then:
    plugin.load.assert_called_once_with()
    plugin.load.return_value.assert_not_called()


def test_load_bad(entry_points: MagicMock) -> None:
    # Given:
    plugin = MagicMock(name="plugin")
    plugin.load.return_value = None
    entry_points.select.return_value = [plugin]
    # When:
    plugins = Plugins(group=None)
    # Then:
    with pytest.warns(PluginWarning, match="neither module nor callable"):
        plugins.load(entry_points.names[0])
