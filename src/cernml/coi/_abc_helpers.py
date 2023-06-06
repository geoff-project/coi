# SPDX-FileCopyrightText: 2020-2023 CERN
# SPDX-FileCopyrightText: 2023 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

"""Provides `check_methods()`, a helper function for ABCs."""

from typing import Any

__all__ = ["check_methods"]


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
