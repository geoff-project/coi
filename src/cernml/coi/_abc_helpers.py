# SPDX-FileCopyrightText: 2020-2024 CERN
# SPDX-FileCopyrightText: 2023-2024 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

"""Provides `check_methods()`, a helper function for ABCs."""

from collections.abc import Mapping
from typing import _get_protocol_attrs  # type: ignore[attr-defined]
from typing import Any, Protocol, _ProtocolMeta

__all__ = (
    "AttrCheckProtocolMeta",
    "AttrCheckProtocol",
)


class AttrCheckProtocolMeta(_ProtocolMeta):
    def __instancecheck__(cls, instance: Any) -> bool:
        is_protocol: bool = getattr(cls, "_is_protocol", False)
        if not is_protocol and issubclass(instance.__class__, cls):
            return True
        if is_protocol:
            if all(
                hasattr(instance, attr)
                and attr_matches(
                    proto_attr=getattr(cls, attr, None),
                    test_attr=getattr(instance, attr),
                )
                for attr in _get_protocol_attrs(cls)
            ):
                return True
        return super().__instancecheck__(instance)


class AttrCheckProtocol(Protocol, metaclass=AttrCheckProtocolMeta):
    @classmethod
    def __subclasshook__(cls, other: type) -> Any:
        # pylint: disable = protected-access
        if not cls.__dict__.get("_is_protocol", False):
            return NotImplemented
        if not isinstance(other, type):
            # Same error message as for issubclass(1, int).
            raise TypeError("issubclass() arg 1 must be a class")
        for attr in _get_protocol_attrs(cls):
            for base in other.__mro__:
                # Check if the members appears in the class dictionary...
                if attr in base.__dict__:
                    if not attr_matches(
                        proto_attr=getattr(cls, attr, None),
                        test_attr=base.__dict__[attr],
                    ):
                        return NotImplemented
                    break

                # ...or in annotations, if it is a sub-protocol.
                annotations = getattr(base, "__annotations__", {})
                if isinstance(annotations, Mapping) and attr in annotations:
                    break
            else:
                return NotImplemented
        return True


def attr_matches(proto_attr: Any, test_attr: Any) -> bool:
    # All *methods* can be blocked by setting them to None.
    return not callable(proto_attr) or (
        isinstance(test_attr, classmethod)
        if isinstance(proto_attr, classmethod)
        else test_attr is not None
    )


def check_methods(C: type, *methods: str) -> Any:
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
    # TODO Switch to using `typing.Protocol` once we no longer support
    # Python 3.7.
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


def check_class_methods(C: type, *methods: str) -> Any:
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
