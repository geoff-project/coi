# SPDX-FileCopyrightText: 2020-2026 CERN
# SPDX-FileCopyrightText: 2023-2026 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

"""Trivial sentinel for `cernml.coi.registration.EnvRegistry.all()`.

Example usage:

    >>> T = typing.TypeVar("T")
    >>> def get_attr(obj: object, name: str, default: "T|Sentinel"=MISSING) -> T:
    ...     attr = vars(obj).get(name, default)
    ...     if attr is MISSING:
    ...         raise AttributeError(f"{obj!r} has not attribute {name!r}")
    ...     return attr
    >>> get_attr(object, "__base__", None) is None
    True
    >>> get_attr(object, "__slots__")
    Traceback (most recent call last):
    ...
    AttributeError: <class 'object'> has not attribute '__slots__'

Example for printing behavior:

    >>> print(MISSING)
    MISSING
    >>> MISSING
    <MISSING>
"""

import enum
import typing

__all__ = (
    "MISSING",
    "Sentinel",
)


@enum.unique
@typing.final
class Sentinel(enum.Enum):
    """Singleton type to mark unpassed arguments.

    This is the default value type of `.EnvRegistry.all()`. The pattern
    is motivated by :pep:`PEP 484
    <484#support-for-singleton-types-in-unions>` and the naming inspired
    by :pep:`PEP 661 <661#specification>`.
    """

    MISSING = "MISSING"

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return self.name.join("<>")


MISSING: Sentinel = Sentinel.MISSING
"""Object used to mark unpassed arguments."""
