# SPDX-FileCopyrightText: 2020-2024 CERN
# SPDX-FileCopyrightText: 2023-2024 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

"""Test inidividual pieces of our protocol machinery."""

import sys
import typing as t
from functools import partial
from types import FunctionType
from unittest.mock import Mock

import pytest

from cernml.coi import _machinery


class Base(t.Protocol):
    base_hint: int
    base_attr: int = 1
    base_no_hint = 2  # type: ignore[misc]

    def base_meth(self) -> None: ...

    @classmethod
    def base_cmeth(cls) -> None: ...


class MyAttrProtocol(_machinery.AttrCheckProtocol, Base):
    hint: int
    attr: int = 1
    no_hint = 2

    def meth(self) -> None: ...

    @classmethod
    def cmeth(cls) -> None: ...


class MyProtocol(Base, t.Protocol):
    hint: int
    attr: int = 1
    no_hint = 2  # type: ignore[misc]

    def meth(self) -> None: ...
    @classmethod
    def cmeth(cls) -> None: ...


@pytest.mark.parametrize(
    ("obj", "expected"),
    [
        (MyAttrProtocol, True),
        (MyProtocol, True),
        (t.Protocol, True),
        (_machinery.AttrCheckProtocol, True),
        (int, False),
        (1, False),
    ],
)
def test_is_protocol(obj: object, expected: bool) -> None:
    assert _machinery.is_protocol(obj) == expected


@pytest.mark.parametrize("cls", [MyAttrProtocol, MyProtocol])
def test_protocol_attrs(cls: t._ProtocolMeta) -> None:
    assert _machinery.protocol_attrs(cls) == {
        "attr",
        "base_attr",
        "base_cmeth",
        "base_hint",
        "base_meth",
        "base_no_hint",
        "cmeth",
        "hint",
        "meth",
        "no_hint",
    }, str(Base.__annotations__)


@pytest.mark.parametrize("cls", [MyAttrProtocol, MyProtocol])
def test_non_callable_proto_members(cls: _machinery.AttrCheckProtocolMeta) -> None:
    assert _machinery.non_callable_proto_members(cls) == {
        "attr",
        "base_attr",
        "base_hint",
        "base_no_hint",
        "hint",
        "no_hint",
    }


def test_non_callable_proto_members_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    class BadDescriptor:
        def __get__(self, instance: object, owner: t.Union[type, None]) -> t.NoReturn:
            raise ValueError

    cls: t.Any = type(
        "MockClass", (), {"__protocol_attrs__": {"cmeth"}, "cmeth": BadDescriptor()}
    )
    with pytest.raises(TypeError, match="^Failed to .* is a method member$"):
        _machinery.non_callable_proto_members(cls)


@pytest.mark.parametrize("cls", [MyAttrProtocol, MyProtocol])
def test_proto_classmethods(cls: _machinery.AttrCheckProtocolMeta) -> None:
    assert _machinery.proto_classmethods(cls) == {"cmeth"}


def test_proto_classmethods_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    def get(key: str, default: object = None) -> object:
        if key == "__proto_classmethods__":
            return None
        if key == "__protocol_attrs__":
            return {"cmeth"}
        raise ValueError

    cls = Mock(name="cls", __proto_classmethods__=None)
    get_dict = Mock(name="get_dict")
    get_dict.return_value.get.side_effect = get
    monkeypatch.setattr(_machinery, "get_dunder_dict_of_class", get_dict)
    with pytest.raises(TypeError, match="^Failed to .* is a classmethod member$"):
        _machinery.proto_classmethods(cls)


def test_attr_check_protocol_dict_empty() -> None:
    """Test __dict__ of the class `AttrCheckProtocol`.

    This ensures that `AttrCheckProtocol` contains nothing that
    `_ProtocolMeta` might interpret as a protocol attribute.
    """
    _get_dict = vars(type)["__dict__"].__get__
    attr_check_protocol_attrs = set(_get_dict(_machinery.AttrCheckProtocol))
    attr_check_protocol_attrs.difference_update(
        {"__annotations__", "__subclasshook__", "__init__"}
    )
    attr_check_protocol_attrs.difference_update(_get_dict(t.Protocol))
    if sys.version_info < (3, 12):
        # Only added to `t.Protocol` in Python 3.12.
        attr_check_protocol_attrs.remove("__protocol_attrs__")
    assert not attr_check_protocol_attrs


@pytest.mark.parametrize("cls", [MyAttrProtocol, MyProtocol])
def test_attr_in_annotations(cls: _machinery.AttrCheckProtocolMeta) -> None:
    check = partial(_machinery.attr_in_annotations, cls)
    annotated_attrs = set(filter(check, _machinery.protocol_attrs(cls)))
    assert annotated_attrs == {"attr", "base_attr", "base_hint", "hint"}


class TestAttrCheckProtocolEdgeCases:
    # Parametrization to ensure that our error message is the same as
    # the built-in one.
    @pytest.mark.parametrize("cls", [MyAttrProtocol, int])
    def test_subclass_not_class(self, cls: type) -> None:
        with pytest.raises(TypeError, match="^issubclass\\(\\) arg 1 must be a class$"):
            cls.__subclasscheck__(1)  # type: ignore[arg-type]

    def test_issubclass_attrcheckprotocol(self) -> None:
        class MyImpl(MyAttrProtocol):
            base_hint = 1
            hint = 2

        assert issubclass(MyImpl, _machinery.AttrCheckProtocol)  # type: ignore[misc]
        assert issubclass(MyAttrProtocol, _machinery.AttrCheckProtocol)  # type: ignore[misc]
        assert not issubclass(int, _machinery.AttrCheckProtocol)  # type: ignore[misc]
        assert issubclass(_machinery.AttrCheckProtocol, t.Protocol)  # type: ignore[arg-type]

    @pytest.mark.xfail(
        sys.version_info < (3, 12),
        strict=True,
        reason="Before Python 3.12, `Protocol` was simply an empty "
        "protocol that matched any type",
    )
    def test_protocol_not_special(self) -> None:
        assert not issubclass(int, t.Protocol)  # type: ignore[arg-type]

    def test_no_protocol_attrs(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def interject(
            cls: type, name: str, bases: tuple[type, ...], namespace: dict[str, object]
        ) -> None:
            namespace.pop("__protocol_attrs__", None)

        monkeypatch.setattr(t._ProtocolMeta, "__init__", interject)

        class MyProto(_machinery.AttrCheckProtocol):
            attr: int

        assert MyProto.__protocol_attrs__ == {"attr"}

    def test_protocol_attrs_preexists(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def interject(
            cls: type, name: str, bases: tuple[type, ...], namespace: dict[str, object]
        ) -> None:
            cls.__protocol_attrs__: set[str] = t._get_protocol_attrs(cls)  # type: ignore[attr-defined,misc]

        monkeypatch.setattr(t._ProtocolMeta, "__init__", interject)

        class MyProto(_machinery.AttrCheckProtocol):
            attr: int

        assert MyProto.__protocol_attrs__ == {"attr"}

    def test_is_protocol_override(self) -> None:
        class WeirdProtocol(MyAttrProtocol):
            _is_protocol = True
            base_hint = 2
            hint = 1

        assert WeirdProtocol._is_protocol

    @pytest.mark.parametrize("cls", [MyAttrProtocol, MyProtocol])
    def test_runtime_checkable(self, cls: type) -> None:
        with pytest.raises(TypeError, match="can only be used with @runtime_checkable"):
            isinstance(None, MyAttrProtocol)

    def test_isinstance_of_attrcheckprotocol(self) -> None:
        @t.runtime_checkable
        class MiniProto(_machinery.AttrCheckProtocol, t.Protocol):
            hint: int

        class DirectImpl(MiniProto):
            hint = 1

        class IndirectImpl:
            hint = 1

        assert isinstance(DirectImpl(), MiniProto)
        assert isinstance(IndirectImpl(), MiniProto)
        assert isinstance(DirectImpl(), _machinery.AttrCheckProtocol)  # type: ignore[misc]
        assert not isinstance(IndirectImpl(), _machinery.AttrCheckProtocol)  # type: ignore[misc]
        assert not isinstance(1, _machinery.AttrCheckProtocol)  # type: ignore[misc]

    @pytest.mark.parametrize("cls", [t.Protocol, _machinery.AttrCheckProtocol])
    def test_isinstance_of_concrete_class(self, cls: type) -> None:
        @t.runtime_checkable
        class MiniProto(cls):  # type: ignore[misc]
            hint: int

        class MyImpl(MiniProto):
            hint = 1

        class UnrelatedImpl:
            hint = 1

        class Subclass(UnrelatedImpl):
            pass

        assert isinstance(MyImpl(), MyImpl)
        assert not isinstance(None, MyImpl)
        assert not isinstance(UnrelatedImpl(), MyImpl)
        assert not isinstance(UnrelatedImpl(), Subclass)

    @pytest.mark.parametrize("mcs", [type, _machinery.AttrCheckProtocolMeta])
    def test_bases_no_tuple(self, mcs: type[type]) -> None:
        # Inherit from AttrCheckProtocol instead of Protocol to enter
        # the section of `__new__` that we want to test.
        bad_bases = {_machinery.AttrCheckProtocol, object}
        with pytest.raises(
            TypeError, match=r"^type\.__new__\(\) argument 2 must be tuple, not set$"
        ):
            mcs("name", t.cast(tuple, bad_bases), {})


class TestAttrsMatch:
    def test_works_direct(self) -> None:
        class MyImpl(MyAttrProtocol):
            base_hint = 1
            hint = 2

        assert _machinery.attrs_match(proto=MyAttrProtocol, obj=MyImpl), "subclass"
        assert _machinery.attrs_match(proto=MyAttrProtocol, obj=MyImpl()), "instance"  # type: ignore[abstract]

    def test_works_indirect(self) -> None:
        class MyImpl:
            base_hint = 100
            base_attr = 111
            base_no_hint = 222
            base_meth = 333

            @classmethod
            def base_cmeth(cls) -> None:
                pass

            hint = 444
            attr = 555
            no_hint = 666
            meth = 777

            @classmethod
            def cmeth(cls) -> None:
                pass

        assert _machinery.attrs_match(proto=MyAttrProtocol, obj=MyImpl), "subclass"
        assert _machinery.attrs_match(proto=MyAttrProtocol, obj=MyImpl()), "instance"

    def test_method_deleted(self) -> None:
        class MyImpl:
            base_hint = 100
            base_attr = 111
            base_no_hint = 222
            base_meth = None

            @classmethod
            def base_cmeth(cls) -> None:
                pass

            hint = 444
            attr = 555
            no_hint = 666
            meth = 777

            @classmethod
            def cmeth(cls) -> None:
                pass

        assert not _machinery.attrs_match(proto=MyAttrProtocol, obj=MyImpl), "subclass"
        assert not _machinery.attrs_match(
            proto=MyAttrProtocol, obj=MyImpl()
        ), "instance"

    def test_missing_attr(self) -> None:
        class MyImpl:
            base_hint = 100
            base_no_hint = 222
            base_meth = None

            @classmethod
            def base_cmeth(cls) -> None:
                pass

            hint = 444
            attr = 555
            no_hint = 666
            meth = 777

            @classmethod
            def cmeth(cls) -> None:
                pass

        assert not _machinery.attrs_match(proto=MyAttrProtocol, obj=MyImpl), "subclass"
        assert not _machinery.attrs_match(
            proto=MyAttrProtocol, obj=MyImpl()
        ), "instance"

    def test_not_classmethod(self) -> None:
        class MyImpl:
            base_hint = 100
            base_no_hint = 222
            base_meth = None

            def base_cmeth(self) -> None:
                pass

            hint = 444
            attr = 555
            no_hint = 666
            meth = 777

            def cmeth(self) -> None:
                pass

        assert not _machinery.attrs_match(proto=MyAttrProtocol, obj=MyImpl), "subclass"
        assert not _machinery.attrs_match(
            proto=MyAttrProtocol, obj=MyImpl()
        ), "instance"

    def test_sub_protocol(self) -> None:
        class MySubProtocol(_machinery.AttrCheckProtocol):
            base_hint: int
            base_attr: int
            base_no_hint: int
            base_meth: int
            base_cmeth: int

            hint: int
            attr: int
            no_hint: int
            meth: int
            cmeth: int

        assert _machinery.attrs_match(proto=MyAttrProtocol, obj=MySubProtocol)


@pytest.mark.parametrize(
    "impl",
    [
        pytest.param(_machinery.get_class_annotations, id="get_class_annotations"),
        pytest.param(
            _machinery.get_class_annotations_impl, id="get_class_annotations_impl"
        ),
    ],
)
class TestGetClassAnnotations:
    def make_type(
        self,
        name: str,
        bases: tuple[tuple[str, tuple[()], dict[str, object]], ...],
        namespace: dict[str, object],
        /,
    ) -> type:
        return type(name, tuple(self.make_type(*args) for args in bases), namespace)

    @pytest.mark.parametrize(
        "type_args",
        [
            pytest.param(("T", (), {}), id="Empty"),
            pytest.param(
                ("T", (("", (), {"__annotations__": {"a": "int"}}),), {}),
                id="BaseAnnotations",
            ),
            pytest.param(("T", (), {"__slots__": ()}), id="SlotType"),
        ],
    )
    def test_empty(
        self,
        impl: t.Callable[[object], dict[str, object]],
        type_args: tuple[str, tuple[tuple, ...], dict[str, object]],
    ) -> None:
        obj = self.make_type(*type_args)
        assert "__annotations__" not in vars(obj)
        res = impl(obj)
        ann = vars(obj)["__annotations__"]
        assert ann == {}
        assert res is ann

    def test_existing_annotations(
        self, impl: t.Callable[[object], dict[str, object]]
    ) -> None:
        obj = type("T", (), {"__annotations__": {"a": "int"}})
        assert "__annotations__" in vars(obj)
        expected = vars(obj)["__annotations__"]
        actual = impl(obj)
        assert expected is actual

    def test_function_type(self, impl: t.Callable[[object], dict[str, object]]) -> None:
        assert "__annotations__" in vars(FunctionType)
        with pytest.raises(
            AttributeError,
            match="type object 'function' has no attribute '__annotations__'",
        ):
            impl(FunctionType)

    def test_type(self, impl: t.Callable[[object], dict[str, object]]) -> None:
        if sys.version_info < (3, 10):
            assert "__annotations__" not in vars(type)
        else:
            assert "__annotations__" in vars(type)
        with pytest.raises(
            AttributeError,
            match="type object 'type' has no attribute '__annotations__'",
        ):
            impl(type)

    def test_object(self, impl: t.Callable[[object], dict[str, object]]) -> None:
        assert "__annotations__" not in vars(object)
        with pytest.raises(
            AttributeError,
            match="type object 'object' has no attribute '__annotations__'",
        ):
            impl(object)
