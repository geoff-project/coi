# SPDX-FileCopyrightText: 2020 - 2025 CERN
# SPDX-FileCopyrightText: 2023 - 2025 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

"""Test global functions of the registration module."""

from __future__ import annotations

import typing as t
from unittest.mock import Mock

import pytest
from gymnasium.envs.registration import EnvSpec as GymEnvSpec

from cernml.coi.registration import EnvRegistry, EnvSpec, errors
from cernml.coi.registration._plugins import Plugins


@pytest.fixture
def registry() -> EnvRegistry:
    magic_namespaces = {"__root__", "__internal__"}
    unloaded = {"ns1", "ns2", "ns3", "__other__"} | magic_namespaces
    registry = EnvRegistry(ep_group=None)

    def load(ns: str, **kwargs: t.Any) -> None:
        if ns not in unloaded:
            return
        unloaded.remove(ns)
        if ns in magic_namespaces:
            name = f"{ns}/name-v1"
            assert registry.current_namespace is None
        else:
            name = "name-v1"
            assert registry.current_namespace == ns
        registry.register(name, entry_point=Mock(name=f"{ns}_entry_point"))

    registry._plugins = Mock(Plugins)
    registry._plugins.unloaded = unloaded
    registry._plugins.load.side_effect = load
    return registry


@pytest.fixture(autouse=True)
def make(monkeypatch: pytest.MonkeyPatch) -> Mock:
    make = Mock(name="make")
    monkeypatch.setattr("cernml.coi.registration._registry.make_impl", make)
    monkeypatch.setattr("cernml.coi.registration._registry.make_vec_impl", make)
    return make


@pytest.fixture(autouse=True)
def import_module(monkeypatch: pytest.MonkeyPatch) -> Mock:
    import_module = Mock(name="import_module")
    monkeypatch.setattr("importlib.import_module", import_module)
    return import_module


def test_namespace(registry: EnvRegistry) -> None:
    ns1 = Mock(name="ns1")
    ns2 = Mock(name="ns2")
    assert registry.current_namespace is None
    with registry.namespace(ns1):
        assert registry.current_namespace == ns1
        with registry.namespace(ns2):
            assert registry.current_namespace == ns2
        assert registry.current_namespace == ns1
    assert registry.current_namespace is None


def test_pprint(registry: EnvRegistry) -> None:
    assert registry.pprint(disable_print=True) == ""
    registry.make("ns1/name-v1")
    registry.make("ns2/name-v1")
    registry.make("ns3/name-v1")
    for v in range(1, 11):
        registry.register(f"name-v{v}", entry_point=Mock())
    res = registry.pprint(disable_print=True)
    assert res == (
        "===== ns1 =====\n"
        "ns1/name-v1\n"
        "===== ns2 =====\n"
        "ns2/name-v1\n"
        "===== ns3 =====\n"
        "ns3/name-v1\n"
        "===== None =====\n"
        "name-v1 name-v10 name-v2\n"
        "name-v3 name-v4 name-v5\n"
        "name-v6 name-v7 name-v8\n"
        "name-v9"
    )


def test_register(registry: EnvRegistry) -> None:
    ep = Mock(name="entry_point")
    registry.register("name", entry_point=ep)
    assert registry.spec("name").entry_point == ep


def test_register_no_entry_point(registry: EnvRegistry) -> None:
    with pytest.raises(ValueError, match="either `\\w+` or `\\w+` must be provided"):
        registry.register("name")


def test_register_overwrite(registry: EnvRegistry) -> None:
    ep = Mock(name="entry_point")
    registry.register("name", entry_point=Mock(name="overwritten"))
    with pytest.warns(errors.EnvSpecExistsWarning):
        registry.register("name", entry_point=ep)
    assert registry.spec("name").entry_point == ep


def test_register_namespace(registry: EnvRegistry) -> None:
    ep = Mock(name="entry_point")
    registry.register("ns/name", entry_point=ep)
    assert registry.spec("ns/name").entry_point == ep


def test_register_namespace_context(registry: EnvRegistry) -> None:
    ep = Mock(name="entry_point")
    with registry.namespace("ns"):
        registry.register("name", entry_point=ep)
    assert registry.spec("ns/name").entry_point == ep


def test_register_namespace_kwarg_ignored(registry: EnvRegistry) -> None:
    ep = Mock(name="entry_point")
    registry.register("name", entry_point=ep, namespace="ns")
    assert registry.spec("name").entry_point == ep


def test_register_ambiguous_namespace(registry: EnvRegistry) -> None:
    ep = Mock(name="entry_point")
    with pytest.warns(errors.AmbiguousNamespaceWarning), registry.namespace("ns"):
        registry.register("name", entry_point=ep, namespace="ignored")
    assert registry.spec("ns/name").entry_point == ep


def test_register_unversioned_after_versioned(registry: EnvRegistry) -> None:
    ep = Mock(name="entry_point")
    registry.register("name-v1", entry_point=ep)
    with pytest.raises(errors.VersionedExistsError):
        registry.register("name", entry_point=Mock(name="fail"))
    with pytest.raises(errors.VersionNotFoundError):
        registry.spec("name")
    assert registry.spec("name-v1").entry_point == ep


def test_register_versioned_after_unversioned(registry: EnvRegistry) -> None:
    ep = Mock(name="entry_point")
    registry.register("name", entry_point=ep)
    with pytest.raises(errors.UnversionedExistsError):
        registry.register("name-v1", entry_point=Mock(name="fail"))
    with pytest.raises(errors.DeprecatedEnv):
        registry.spec("name-v1")
    assert registry.spec("name").entry_point == ep


def test_all(registry: EnvRegistry) -> None:
    ep = Mock(name="entry_point")
    registry.register("name", entry_point=ep)
    assert all(spec.entry_point == ep for spec in registry.all(version=None))


def test_spec(registry: EnvRegistry) -> None:
    ep = Mock(name="entry_point")
    registry.register("name", entry_point=ep)
    assert registry.spec("name").entry_point == ep


def test_spec_does_not_import(registry: EnvRegistry) -> None:
    ep = Mock(name="entry_point")
    registry.register("name", entry_point=ep)
    with pytest.raises(errors.NameNotFoundError):
        registry.spec("import:name")


def test_spec_does_not_auto_load(registry: EnvRegistry) -> None:
    with pytest.raises(errors.NamespaceNotFoundError):
        registry.spec("ns1/name-v1")


def test_make_default_args(registry: EnvRegistry, make: Mock) -> None:
    spec = EnvSpec("name")
    res = registry.make(spec)
    assert res == make.return_value
    make.assert_called_once_with(
        spec,
        max_episode_steps=None,
        autoreset=None,
        apply_api_compatibility=None,
        disable_env_checker=None,
        order_enforce=None,
        stacklevel=3,
    )


def test_make_vec_default_args(registry: EnvRegistry, make: Mock) -> None:
    spec = EnvSpec("name")
    res = registry.make_vec(spec)
    assert res == make.return_value
    make.assert_called_once_with(
        GymEnvSpec("name"),
        num_envs=1,
        vectorization_mode="async",
        vector_kwargs=None,
        wrappers=None,
    )


class TestMake:
    @pytest.fixture
    def _make_not_called(self, make: Mock) -> t.Iterator[None]:
        yield
        if make.called:
            pytest.fail(
                f"Expected 'make' to have not been called. "
                f"Called {make.call_count} times."
            )

    @pytest.fixture(params=["make", "make_vec"])
    def make_either(
        self, registry: EnvRegistry, request: pytest.FixtureRequest
    ) -> t.Callable:
        return getattr(registry, request.param)

    def test_make_forwards_env_spec(self, make_either: t.Callable, make: Mock) -> None:
        spec = EnvSpec("name")
        res = make_either(spec)
        assert res == make.return_value
        assert make.call_args[0][0].name == "name"

    @pytest.mark.usefixtures("_make_not_called")
    def test_make_env_not_found(self, make_either: t.Callable) -> None:
        with pytest.raises(errors.NotFoundError):
            make_either("name")

    @pytest.mark.usefixtures("_make_not_called")
    def test_make_spec_type_error(self, make_either: t.Callable) -> None:
        with pytest.raises(TypeError):
            make_either(t.cast(t.Any, 1))

    def test_make_auto_load(
        self, make_either: t.Callable, registry: EnvRegistry, make: Mock
    ) -> None:
        with pytest.raises(errors.NotFoundError):
            registry.spec("ns1/name-v1")
        res = make_either("ns1/name-v1")
        assert res == make.return_value
        assert registry.spec("ns1/name-v1").namespace == "ns1"

    @pytest.mark.parametrize("ns", ["__root__", "__internal__"])
    def test_make_auto_load_magic_namespace(
        self, make_either: t.Callable, registry: EnvRegistry, make: Mock, ns: str
    ) -> None:
        with pytest.raises(errors.NotFoundError):
            registry.spec(f"{ns}/name-v1")
        res = make_either(f"{ns}/name-v1")
        assert res == make.return_value
        assert registry.spec(f"{ns}/name-v1").namespace == ns

    def test_make_auto_load_deprecated_namespace(
        self, make_either: t.Callable, registry: EnvRegistry, make: Mock
    ) -> None:
        with pytest.raises(errors.NotFoundError):
            registry.spec("__other__/name-v1")
        with pytest.warns(errors.GymDeprecationWarning, match="__root__"):
            res = make_either("__other__/name-v1")
        assert res == make.return_value
        assert registry.spec("__other__/name-v1").namespace == "__other__"

    def test_make_import_module(
        self,
        make_either: t.Callable,
        registry: EnvRegistry,
        make: Mock,
        import_module: Mock,
    ) -> None:
        with pytest.raises(errors.NotFoundError):
            registry.spec("name")
        import_module.side_effect = lambda _: registry.register(
            "name", entry_point=Mock(name="entry_point")
        )
        res = make_either("modname:name")
        assert res == make.return_value
        import_module.assert_called_once_with("modname")
        assert registry.spec("name")

    def test_make_import_module_disallowed(
        self, make_either: t.Callable, import_module: Mock
    ) -> None:
        with pytest.raises(errors.EnvImportError, match="imports have been disabled"):
            make_either("modname:name", allow_imports=False)
        import_module.assert_not_called()

    def test_make_import_module_fails(
        self, make_either: t.Callable, import_module: Mock
    ) -> None:
        import_module.side_effect = ModuleNotFoundError
        with pytest.raises(ModuleNotFoundError):
            make_either("modname:name")
        import_module.side_effect = TypeError
        with pytest.raises(
            errors.EnvImportError, match="module 'modname' to make env 'name'"
        ):
            make_either("modname:name")

    def test_make_auto_upgrade(
        self, make_either: t.Callable, registry: EnvRegistry, make: Mock
    ) -> None:
        ep1 = Mock(name="entry_point_1")
        ep2 = Mock(name="entry_point_2")
        registry.register("name-v1", entry_point=ep1)
        registry.register("name-v2", entry_point=ep2)
        with pytest.warns(errors.EnvUpgradedWarning, match="v2"):
            make_either("name")
        with pytest.warns(errors.EnvOutOfDateWarning, match="v2"):
            make_either("name-v1")
        assert make.call_args_list[0][0][0].id == "name-v2"
        assert make.call_args_list[1][0][0].id == "name-v1"
