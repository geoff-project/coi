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
            pass
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
        if cls is t.Protocol:
            return type.__instancecheck__(cls, instance)
        if not getattr(cls, "_is_protocol", False):
            # i.e., it's a concrete subclass of a protocol
            return super().__instancecheck__(instance)
        if not getattr(cls, "_is_runtime_protocol", False):
            raise TypeError(
                "Instance and class checks can only be used with"
                " @runtime_checkable protocols"
            )
        if super().__instancecheck__(instance):
            return True
        return _attrs_match(cls, instance)

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
    if not _attrs_match(cls, other):
        return NotImplemented
    return True


def _attrs_match(proto: AttrCheckProtocolMeta, obj: object) -> bool:
    getattr_static = _lazy_load_getattr_static()
    for attr in proto.__protocol_attrs__:
        is_classmethod = attr in _proto_classmethods(proto)
        try:
            val = getattr_static(
                type(obj) if is_classmethod and not isinstance(obj, type) else obj, attr
            )
        except AttributeError:
            if not _is_subprotocol(obj) or not _attr_in_annotations(obj, attr):
                return False
        else:
            if is_classmethod:
                if not isinstance(val, classmethod):
                    return False
            else:
                if val is None and attr not in _non_callable_proto_members(proto):
                    return False
    return True


def _is_subprotocol(obj: object) -> "TypeGuard[AttrCheckProtocolMeta]":
    return (
        isinstance(obj, type)
        and issubclass(obj, t.Generic)  # type: ignore[arg-type]
        and getattr(obj, "_is_protocol", False)
    )


def _attr_in_annotations(proto: AttrCheckProtocolMeta, attr: str) -> bool:
    for base in _static_mro(proto):
        try:
            annotations = _static_annotations(base)
        except AttributeError:
            continue
        if isinstance(annotations, Mapping) and attr in annotations:
            return True
    return False


def _non_callable_proto_members(cls: AttrCheckProtocolMeta) -> set[str]:
    """Reproduction of Python 3.12+ `@runtime_checkable`."""
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


def _proto_classmethods(cls: AttrCheckProtocolMeta) -> set[str]:
    """Reproduction of Python 3.12+ `@runtime_checkable`."""
    members = getattr(cls, "__proto_classmethods__", None)
    if members is None:
        members = set()
        for attr in _non_callable_proto_members(cls):
            try:
                is_classmethod = isinstance(getattr(cls, attr, None), classmethod)
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
def _lazy_load_getattr_static() -> "_GetAttr":
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
        >>> class MyProtocol(AttrCheckProtocol):
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

        >>> class Bad1:
        ...     def meth(self): pass
        ...     def c_meth(self): pass
        ...     attr = {}
        ...
        >>> isinstance(Bad1(), MyProtocol)
        False
        >>> issubclass(Bad1, MyProtocol)
        False
        >>> class Bad1:
        ...     def meth(self): pass
        ...     def c_meth(self): pass
        ...     attr = {}
        ...
        >>> isinstance(Bad1(), MyProtocol)
        False
        >>> issubclass(Bad1, MyProtocol)
        False
        >>> class Bad1:
        ...     def meth(self): pass
        ...     def c_meth(self): pass
        ...     attr = {}
        ...
        >>> isinstance(Bad1(), MyProtocol)
        False
        >>> issubclass(Bad1, MyProtocol)
        False
        >>> class Bad1:
        ...     def meth(self): pass
        ...     def c_meth(self): pass
        ...     attr = {}
        ...
        >>> isinstance(Bad1(), MyProtocol)
        False
        >>> issubclass(Bad1, MyProtocol)
        False
    """


def check_methods(C: type, *methods: str) -> t.Any:
    """Check whether the class ``C`` provides all given methods.

    Methods are searched in ``C`` and all its bases, but not in
    instances of ``C``. Only the name is checked, not the signature.

    If the method is found, but explicitly set to None, the method is
    considered unimplemented, even if a superclass provides it.

    Args:
        C: The class to be checked.
        methods: The names of methods to be searched for.

    Returns:
        True if ``C`` implements all given methods, otherwise
        `NotImplemented`.

    Examples:

        >>> from abc import ABC
        >>> class Protocol(ABC):
        ...     def some_method(self) -> str:
        ...         raise NotImplementedError()
        ...     @classmethod
        ...     def __subclasshook__(cls, other: type) -> Any:
        ...         if cls is Protocol:
        ...             return check_methods(other, "some_method")
        ...         return NotImplemented
        >>> class SatisfiesProtocol:
        ...     def some_method(self):
        ...         return 'foo'
        >>> issubclass(SatisfiesProtocol, Protocol)
        True
        >>> class FailsProtocol:
        ...     def some_other_method(self):
        ...         return 'foo'
        >>> issubclass(FailsProtocol, Protocol)
        False
        >>> class DisablesProtocol:
        ...     some_method = None
        >>> issubclass(DisablesProtocol, Protocol)
        False
    """
    # pylint: disable = invalid-name
    # Original implementation:
    # https://github.com/python/cpython/blob/v3.7.0/Lib/_collections_abc.py#L72
    # See also the more general solution:
    # https://github.com/python/cpython/blob/v3.7.0/Lib/typing.py#L1100
    mro = C.__mro__
    for method in methods:
        for B in mro:
            if method in B.__dict__:
                if B.__dict__[method] is None:
                    return NotImplemented
                break
        else:
            return NotImplemented
    return True


def check_class_methods(C: type, *methods: str) -> t.Any:
    """Like `check_methods()` with additional `classmethod` check.

    Args:
        C: The class to be checked.
        methods: The names of methods to be searched for.

    Returns:
        True if ``C`` implements all given methods, otherwise
        `NotImplemented`.

    Examples:

        >>> from abc import ABC
        >>> class Protocol(ABC):
        ...     def some_method(self) -> str:
        ...         raise NotImplementedError()
        ...     @classmethod
        ...     def __subclasshook__(cls, other: type) -> Any:
        ...         if cls is Protocol:
        ...             return check_class_methods(other, "cm")
        ...         return NotImplemented
        ...
        >>> class SatisfiesProtocol:
        ...     @classmethod
        ...     def cm(cls):
        ...         pass
        >>> issubclass(SatisfiesProtocol, Protocol)
        True
        >>> class FailsProtocol:
        ...     def other_method(self):
        ...         pass
        >>> issubclass(FailsProtocol, Protocol)
        False
        >>> class OnlyHasInstanceMethod:
        ...     def cm(self):
        ...         pass
        >>> issubclass(FailsProtocol, Protocol)
        False
        >>> class DisablesProtocol:
        ...     cm = None
        >>> issubclass(DisablesProtocol, Protocol)
        False
    """
    # pylint: disable = invalid-name
    mro = C.__mro__
    for method in methods:
        for B in mro:
            if method in B.__dict__:
                obj = B.__dict__[method]
                if obj is None or not isinstance(obj, classmethod):
                    return NotImplemented
                break
        else:
            return NotImplemented
    return True
