# SPDX-FileCopyrightText: 2020 - 2025 CERN
# SPDX-FileCopyrightText: 2023 - 2025 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

"""Test that `Problem` does not require direct inheritance."""

from __future__ import annotations

import typing as t
from unittest.mock import Mock

import pytest

from cernml import coi


def test_has_np_random() -> None:
    class Subclass(coi.HasNpRandom):
        pass

    instance = Subclass()
    assert instance.np_random is instance.np_random
    assert instance.np_random.uniform() < 2
    instance.np_random = None  # type: ignore[assignment]
    assert instance.np_random.uniform() < 2


class TestProtocol:
    def test_protocol_attrs(self) -> None:
        assert getattr(coi.protocols.Problem, "__protocol_attrs__", None) == {
            "close",
            "get_wrapper_attr",
            "metadata",
            "render",
            "render_mode",
            "spec",
            "unwrapped",
        }

    def test_non_callable_proto_members(self) -> None:
        assert getattr(
            coi.protocols.Problem, "__non_callable_proto_members__", None
        ) == {
            "metadata",
            "render_mode",
            "spec",
            "unwrapped",
        }

    def test_proto_classmethods__(self) -> None:
        assert getattr(coi.protocols.Problem, "__proto_classmethods__", None) == set()

    def test_is_abstract(self) -> None:
        class NonInheritingProblem:
            metadata: t.ClassVar[dict[str, t.Any]] = {"render_modes": []}
            render_mode = None
            spec = None

            def close(self) -> None:
                pass

            def render(self, mode: str = "human") -> t.Any:
                raise NotImplementedError

            @property
            def unwrapped(self) -> "NonInheritingProblem":
                return self

            def get_wrapper_attr(self, name: str) -> t.Any:
                return getattr(self, name)

        assert issubclass(NonInheritingProblem, coi.protocols.Problem)  # type: ignore[misc]

    def test_render_raises(self) -> None:
        class Subclass(coi.protocols.Problem):
            pass

        env = Subclass()
        with pytest.raises(NotImplementedError):
            env.render()

    def test_requires_get_wrapper_attr(self) -> None:
        class NullProblemo:
            metadata: t.ClassVar[dict[str, t.Any]] = {"render_modes": []}

            def render(self, mode: str = "human") -> t.Any:
                raise NotImplementedError

            def unwrapped(self) -> "NullProblemo":
                return self

            def close(self) -> None:
                pass

        assert not coi.is_problem_class(NullProblemo)

    def test_get_wrapper_attr_is_getattr(self) -> None:
        class Subclass(coi.protocols.Problem):
            def __init__(self) -> None:
                self.test = Mock()

        instance = Subclass()
        assert instance.get_wrapper_attr("test") == instance.test

    def test_requires_close(self) -> None:
        class NullProblemo:
            metadata: t.ClassVar[dict[str, t.Any]] = {"render_modes": []}

            def render(self, mode: str = "human") -> t.Any:
                raise NotImplementedError

            def unwrapped(self) -> "NullProblemo":
                return self

            def get_wrapper_attr(self, name: str) -> t.Any:
                return getattr(self, name)

        assert not coi.is_problem_class(NullProblemo)

    def test_close_returns_none(self) -> None:
        class Subclass(coi.protocols.Problem):
            pass

        assert Subclass().close() is None  # type: ignore[func-returns-value]

    def test_render_mode_property(self) -> None:
        class Subclass(coi.protocols.Problem):
            render_mode: str | None = None

            def __init__(self, render_mode: str | None = None) -> None:
                self.render_mode = render_mode

        instance = Subclass(render_mode="human")
        assert instance.render_mode == "human"
        assert coi.protocols.Problem.render_mode.__get__(instance) == "human"

    def test_spec_property(self) -> None:
        class Subclass(coi.protocols.Problem):
            spec: coi.registration.EnvSpec | None = None

        instance = Subclass()
        instance.spec = coi.registration.EnvSpec("_")
        assert instance.spec == coi.registration.EnvSpec("_")
        assert coi.protocols.Problem.spec.__get__(instance) == coi.registration.EnvSpec(
            "_"
        )


class TestProblem:
    def test_is_problem_through_protocol(self) -> None:
        assert coi.is_problem_class(coi.Problem)
        assert issubclass(coi.Problem, coi.protocols.Problem)  # type: ignore[misc]
        assert coi.protocols.Problem not in coi.Problem.__mro__

    @pytest.mark.parametrize("render_mode", ["human", None])
    def test_sets_render_mode(self, render_mode: str | None) -> None:
        class Subclass(coi.Problem):
            metadata = {"render_modes": ["human"]}

        env = Subclass(render_mode=render_mode)
        assert env.render_mode == render_mode

    def test_warn_deprecated_render_modes(self) -> None:
        class Subclass(coi.Problem):
            metadata = {"render.modes": [], "render_modes": ["human"]}

        with pytest.warns(DeprecationWarning):
            Subclass(render_mode="human")

    def test_use_deprecated_render_modes_without_new_modes(self) -> None:
        class Subclass(coi.Problem):
            metadata = {"render.modes": ["human"]}

        with pytest.warns(DeprecationWarning):
            Subclass(render_mode="human")

    def test_reject_bad_render_mode(self) -> None:
        class Subclass(coi.Problem):
            metadata = {}

        with pytest.raises(ValueError, match="invalid render mode"):
            Subclass(render_mode="human")

    def test_context_manager(self) -> None:
        env = coi.Problem()
        env.close = Mock(wraps=env.close)  # type: ignore[method-assign]
        with env as ctx:
            assert ctx is env
        env.close.assert_called_once_with()

    def test_get_wrapper_attr_is_getattr(self) -> None:
        class Subclass(coi.Problem):
            def __init__(self) -> None:
                self.test = Mock()

        instance = Subclass()
        assert instance.get_wrapper_attr("test") == instance.test


@pytest.mark.parametrize(
    ("cls", "proto"),
    [
        (coi.Problem, coi.protocols.Problem),
        (coi.SingleOptimizable, coi.protocols.SingleOptimizable),
        (coi.FunctionOptimizable, coi.protocols.FunctionOptimizable),
    ],
)
class TestClasses:
    def test_dir(self, cls: type, proto: type) -> None:
        expected = {name for name in dir(proto) if not name.startswith("_")}
        expected.add("np_random")
        if cls is coi.SingleOptimizable:
            # Because coi.SingleOptimizable isn't a protocol and
            # `optimization_space` is defined only as a type annotation,
            # `dir()` does not find it.
            expected.remove("optimization_space")
        actual = {name for name in dir(cls) if not name.startswith("_")}
        assert actual == expected

    def test_subclasshook(self, cls: type, proto: type) -> None:
        impl = type("Impl", (cls,), {})
        assert issubclass(impl, impl)
        assert issubclass(impl, cls)
        assert issubclass(impl, proto)
        assert not issubclass(cls, impl)
        assert issubclass(cls, cls)
        assert issubclass(cls, proto)
        assert not issubclass(proto, impl)
        assert not issubclass(proto, cls)
        assert issubclass(proto, proto)
