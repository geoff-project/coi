# SPDX-FileCopyrightText: 2020-2024 CERN
# SPDX-FileCopyrightText: 2023-2024 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

"""Test inidividual pieces of our protocol machinery."""

import typing as t
from functools import partial

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
def test_is_subprotocol(obj: object, expected: bool) -> None:
    assert _machinery.is_subprotocol(obj) == expected


@pytest.mark.parametrize("cls", [MyAttrProtocol, MyProtocol])
def test_protocol_attrs(cls: t._ProtocolMeta) -> None:
    assert cls.__protocol_attrs__ == {  # type: ignore[attr-defined]
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


@pytest.mark.parametrize("cls", [MyAttrProtocol, MyProtocol])
def test_proto_classmethods(cls: _machinery.AttrCheckProtocolMeta) -> None:
    assert _machinery.proto_classmethods(cls) == {"cmeth"}


def test_attr_check_protocol_dict_empty() -> None:
    # This ensures that `AttrCheckProtocol` contains nothing that
    # `_ProtocolMeta` might interpret as a protocol attribute
    _get_dict = vars(type)["__dict__"].__get__
    attr_check_protocol_attrs = set(_get_dict(_machinery.AttrCheckProtocol))
    attr_check_protocol_attrs.difference_update(
        {"__annotations__", "__subclasshook__", "__init__"}
    )
    attr_check_protocol_attrs.difference_update(_get_dict(t.Protocol))
    assert not attr_check_protocol_attrs


@pytest.mark.parametrize("cls", [MyAttrProtocol, MyProtocol])
def test_attr_in_annotations(cls: _machinery.AttrCheckProtocolMeta) -> None:
    check = partial(_machinery.attr_in_annotations, cls)
    annotated_attrs = set(filter(check, cls.__protocol_attrs__))
    assert annotated_attrs == {"attr", "base_attr", "base_hint", "hint"}


def test_attrs_match() -> None:
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


def test_attrs_match_method_none() -> None:
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
    assert not _machinery.attrs_match(proto=MyAttrProtocol, obj=MyImpl()), "instance"


def test_attrs_match_missing_attr() -> None:
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
    assert not _machinery.attrs_match(proto=MyAttrProtocol, obj=MyImpl()), "instance"


def test_attrs_match_not_classmethod() -> None:
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
    assert not _machinery.attrs_match(proto=MyAttrProtocol, obj=MyImpl()), "instance"
