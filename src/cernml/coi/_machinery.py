# SPDX-FileCopyrightText: 2020-2024 CERN
# SPDX-FileCopyrightText: 2023-2024 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

# You know some real FUN is going to happen!
# pylint: disable = import-outside-toplevel
# pylint: disable = protected-access
# pylint: disable = unsupported-membership-test

"""Provide the internal machinery for `Problem`."""

import functools
import typing as t
from abc import ABCMeta
from collections.abc import Mapping

if t.TYPE_CHECKING:
    from typing_extensions import TypeGuard

__all__ = (
    "AttrCheckProtocolMeta",
    "AttrCheckProtocol",
)


_static_mro: t.Callable[[type], tuple[type, ...]] = vars(type)["__mro__"].__get__
_static_annotations: t.Callable[[type], t.Any] = vars(type)["__annotations__"].__get__
_get_dunder_dict_of_class: t.Callable[[object], dict[str, t.Any]] = vars(type)[
    "__dict__"
].__get__


class AttrCheckProtocolMeta(t._ProtocolMeta):
    """The metaclass of `AttrCheckProtocol`.

    This contains the actual implementation of the protocol checking
    logic. `AttrCheckProtocol` itself is a trivial instance of this
    metaclass.
    """

    def __new__(
        mcs,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, t.Any],
        /,
        **kwargs: t.Any,
    ) -> "AttrCheckProtocolMeta":
        # Supply our own `is_protocol` and `__subclasshook__` that
        # override those of `typing.Protocol`. This is the only place
        # where we can inject them, because:
        # 1) `Protocol` adds them in `Protocol.__init_subclass__`, which
        #    is called as part of `type.__new__()`.
        # 2) We can't add our own
        #    `AttrCheckProtocol.__init_subclass__()` because
        #    `typing._get_protocol_attrs()` would find that as
        #    a protocol method.
        if name == "AttrCheckProtocol" and bases == (t.Protocol,):
            namespace["_is_protocol"] = True
            namespace["_is_runtime_protocol"] = False
        elif not namespace.get("_is_protocol", False):
            namespace["_is_protocol"] = any(b is AttrCheckProtocol for b in bases)
        namespace.setdefault("__subclasshook__", _proto_hook)
        return super().__new__(mcs, name, bases, namespace, **kwargs)

    def __init__(cls, *args: t.Any, **kwargs: t.Any) -> None:
        super().__init__(*args, **kwargs)
        if getattr(cls, "_is_protocol", False) and not hasattr(
            cls, "__protocol_attrs__"
        ):
            attrs = t._get_protocol_attrs(cls)  # type: ignore[attr-defined]
            cls.__protocol_attrs__: set[str] = attrs

    def __instancecheck__(cls, instance: t.Any) -> bool:
        if cls is AttrCheckProtocol:
            return type.__instancecheck__(cls, instance)
        if not getattr(cls, "_is_protocol", False):
            # i.e., it's a concrete subclass of a protocol
            return super().__instancecheck__(instance)
        if not getattr(cls, "_is_runtime_protocol", False):
            raise TypeError(
                "Instance and class checks can only be used with"
                " @runtime_checkable protocols"
            )
        # Skip _ProtocolMeta.__instancecheck__, it runs through the
        # attribute list with the primitive test we want to avoid.
        if ABCMeta.__instancecheck__(cls, instance):
            return True
        return attrs_match(cls, instance)

    def __subclasscheck__(cls, other: type) -> bool:
        # Do not let `AttrCheckProtocol` itself go through the
        # `Protocol` machinery!
        if cls is AttrCheckProtocol:
            return type.__subclasscheck__(cls, other)
        return super().__subclasscheck__(other)

    def __dir__(cls) -> t.Iterable[str]:
        # Include protocol members that only exist as annotations.
        # Without this. `unittest.Mock()` won't be able to auto-spec
        # these members
        attrs = super().__dir__()
        annotations = set(cls.__protocol_attrs__)
        return sorted(set(attrs) | annotations)


@classmethod  # type: ignore[misc]
def _proto_hook(cls: AttrCheckProtocolMeta, other: type) -> t.Any:
    # pylint: disable = protected-access
    if not cls.__dict__.get("_is_protocol", False):
        return NotImplemented
    if not isinstance(other, type):
        # Same error message as for issubclass(1, int).
        raise TypeError("issubclass() arg 1 must be a class")
    if not attrs_match(cls, other):
        return NotImplemented
    return True


def attrs_match(proto: AttrCheckProtocolMeta, obj: object) -> bool:
    """Check if the attributes of *obj* match those of *proto*.

    This is the core logic of `AttrCheckProtocol`, called by both
    `isinstance()` and `issubclass()`. It iterates over all protocol
    members (which have been cached at class creation) and attempts to
    access each one on *obj* via `inspect.getattr_static()`.

    If *obj* is itself a protocol, its annotations (and those of its
    base classes) are checked as well.

    If an attribute is a method on the protocol, any object except
    `None` is accepted on *obj*.

    If an attribute is a classmethod on the protocol, it must be one on
    *obj* as well.

    If an attribute is neither a method nor a classmethod, any value is
    accepted on *obj*.
    """
    getattr_static = lazy_load_getattr_static()
    for attr in proto.__protocol_attrs__:
        is_classmethod = attr in proto_classmethods(proto)
        try:
            val = getattr_static(
                type(obj) if is_classmethod and not isinstance(obj, type) else obj, attr
            )
        except AttributeError:
            if not is_subprotocol(obj) or not attr_in_annotations(obj, attr):
                return False
        else:
            if is_classmethod:
                if not isinstance(val, classmethod):
                    return False
            elif val is None and attr not in non_callable_proto_members(proto):
                return False
    return True


def is_subprotocol(obj: object) -> "TypeGuard[AttrCheckProtocolMeta]":
    """Check whether *obj* is a subclass of `Protocol`.

    This has been copied from Python 3.12+ `_ProtocolMeta.__new__()`.
    """
    return (
        isinstance(obj, type)
        and issubclass(obj, t.Generic)  # type: ignore[arg-type]
        and getattr(obj, "_is_protocol", False)
    )


def attr_in_annotations(proto: AttrCheckProtocolMeta, attr: str) -> bool:
    """Check if *proto* or anything in its MRO annotate *attr*.

    This check is necessary because attributes of a protocol may be
    merely annotated (but not defined), in which case `getattr_static()`
    won't find them.

    This code is modified from Python 3.12+ `typing._proto_hook()`.
    """
    for base in _static_mro(proto):
        try:
            annotations = _static_annotations(base)
        except AttributeError:
            continue
        if isinstance(annotations, Mapping) and attr in annotations:
            return True
    return False


def non_callable_proto_members(cls: AttrCheckProtocolMeta) -> set[str]:
    """Lazy collection of any protocol members that aren't methods.

    Note that this does not include classmethods. Classmethod objects
    themselves are not callable; however, we collect them with
    `getattr(cls, name)`. This returns a bound method object, which _is_
    callable!

    The result is cached in the class's `__non_callable_proto_members__`
    attribute. If it already exists (which is the case on Python 3.12+),
    it is returned directly.

    This code is modified from Python 3.12+ `@runtime_checkable`.
    """
    members = getattr(cls, "__non_callable_proto_members__", None)
    if members is None:
        members = set()
        for attr in cls.__protocol_attrs__:
            try:
                is_callable = callable(getattr(cls, attr, None))
            except Exception as e:
                raise TypeError(
                    f"Failed to determine whether protocol member {attr!r} "
                    f"is a method member"
                ) from e
            if not is_callable:
                members.add(attr)
        cls.__non_callable_proto_members__ = members  # type: ignore[attr-defined]
    return members


def proto_classmethods(cls: AttrCheckProtocolMeta) -> set[str]:
    """Lazy collection of any protocol classmethods.

    Whether an object is a classmethod is tested by `isinstance()` check
    against `classmethod`. Note that at least on CPython, this is true
    even for implicit classmethods like `object.__init_subclass__()` and
    `object.__class_getitem__()`.

    The result is cached in the class's `__proto_classmethods__`
    attribute.

    This code is based on `non_callable_proto_members()`, which is in
    turn modified from Python 3.12+ `@runtime_checkable`.
    """
    members = getattr(cls, "__proto_classmethods__", None)
    if members is None:
        # Access the attributes via the class dictionary; access
        # via `getattr()` would bind them and give us bound-method
        # objects, not classmethod objects!
        cvars = _get_dunder_dict_of_class(cls)
        members = set()
        for attr in cls.__protocol_attrs__:
            try:
                is_classmethod = isinstance(cvars.get(attr, None), classmethod)
            except Exception as e:
                raise TypeError(
                    f"Failed to determine whether protocol member {attr!r} "
                    f"is a classmethod member"
                ) from e
            if is_classmethod:
                members.add(attr)
        cls.__proto_classmethods__ = members  # type: ignore[attr-defined]
    return members


@functools.cache
def lazy_load_getattr_static() -> "_GetAttr":
    """Lazy loader for `inspect.getattr_static()`.

    This delays loading the `inspect` module until the first
    instance/subclass check against an `AttrCheckProtocol`, since the
    module is rather heavy. This has been copied from the Python 3.12+
    `typing` module.
    """
    # Copied from typing.py.
    from inspect import getattr_static

    return getattr_static


class _GetAttr(t.Protocol):
    def __call__(
        self, obj: object, name: str, default: t.Optional[t.Any] = ..., /
    ) -> t.Any: ...


class AttrCheckProtocol(t.Protocol, metaclass=AttrCheckProtocolMeta):
    """Extension of `typing.Protocol` to check attributes and classmethods.

    Subclassing `AttrCheckProtocol` is largely the same as subclassing
    `~typing.Protocol` directly. However, when creating
    a `~typing.runtime_checkable` protocol using `AttrCheckProtocol`, it
    will work with `issubclass()` *even if* your protocol defines
    attributes, properties or class methods.

    Protocol members are collected in the same way as in Python 3.12+,
    meaning at class creation time. You can monkey-patch a protocol with
    additional methods or attributes, but those will not be considered
    in the `isinstance()` and `issubclass()` checks.

    The `isinstance()` check aligns with Python 3.12+. However, for each
    protocol member that is a `@classmethod`, it additionally tests that
    the class of the tested instance provides a `classmethod` as well.
    Properties and normal functions are rejected.

    Checks with `issubclass()` work even if the protocol defines
    non-method members. Protocol classmethods are tested similarly to
    `isinstance()` checks, except on the subclass directly (and not on
    its metaclass).

    Checks with `issubclass()` for regular protocol methods are stricter
    than for `typing.Protocol`. Not only must the subclass have an
    attribute of the same name, it must also be callable (like for
    `isinstance()` checks).

    Just like with `typing.Protocol`, checks with `issubclass()` may
    also be satisfied if the tested subclass is itself a protocol and
    contains an *annotation* with the same name as a protocol attribute.
    Classmethods are treated like other attributes here.

    Examples:

        >>> from typing import Any, runtime_checkable
        ...
        >>> @runtime_checkable
        ... class MyProtocol(AttrCheckProtocol):
        ...     def meth(self): pass
        ...     @classmethod
        ...     def c_meth(cls): pass
        ...     attr: dict[str, Any]
        ...

    Other objects must at least contain the specified attributes to
    implement the protocol:

        >>> class Good:
        ...     def meth(self): pass
        ...     @classmethod
        ...     def c_meth(cls): pass
        ...     attr = {}
        ...
        >>> isinstance(Good(), MyProtocol)
        True
        >>> issubclass(Good, MyProtocol)
        True
        >>> isinstance(1, MyProtocol)
        False
        >>> issubclass(int, MyProtocol)
        False

    A regular method in place of a classmethod is rejected:

        >>> class Bad:
        ...     def meth(self): pass
        ...     def c_meth(self): pass
        ...     attr = {}
        ...
        >>> isinstance(Bad(), MyProtocol)
        False
        >>> issubclass(Bad, MyProtocol)
        False
    """

    __slots__ = ()
