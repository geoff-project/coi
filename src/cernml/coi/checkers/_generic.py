# SPDX-FileCopyrightText: 2020-2024 CERN
# SPDX-FileCopyrightText: 2023-2024 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

"""Generic assertions and checks used by multiple checkers."""

import typing as t

import gymnasium as gym
import numpy as np
import typing_extensions as tx

# TODO: Add proper version guards around tx


def bump_warn_arg(warn: int) -> int:
    """Increase the warn argument if it's nonzero.

    If *warn* is False, it is returned unmodified. Otherwise, it's set
    to at least 2 before being increased by 1 and returned.

    The ``min()`` in the middle ensures that warnings are always
    reported at least in the caller of our functions.

    The purpose of increasing the argument is so that warnings are
    always reported outside of this package. This is necessary because
    `~warnings.warn()` only supports the *skip_file_prefixes* parameter
    in Python 3.12+.

    Example:

        >>> bump_warn_arg(False)
        False
        >>> bump_warn_arg(True)
        3
        >>> bump_warn_arg(1)
        3
        >>> bump_warn_arg(2)
        3
        >>> bump_warn_arg(10)
        11
    """
    return warn and max(warn, 2) + 1


def assert_range(reward_range: t.Tuple[float, float], name: str) -> None:
    """Check that the reward range is actually a range."""
    assert len(reward_range) == 2, f"{name} reward range must be tuple `(low, high)`."
    low, high = reward_range
    assert low <= high, f"lower bound of {name} range must be lower than upper bound"


def is_reward(reward: t.Any) -> tx.TypeGuard[t.SupportsFloat]:
    """Return True if the object has the correct type for a reward."""
    return isinstance(reward, t.SupportsFloat)


def is_bool(value: t.Any) -> tx.TypeGuard[t.Union[bool, np.bool_]]:
    """Return True if the object is a true boolean.

    This accepts `bool`, :class:`np.bool_` and possible subclasses, but
    it rejects integers. (This is nontrivial because Python booleans
    *are* integers.)

    Example:

        >>> is_bool(True)
        True
        >>> is_bool(np.bool_(0))
        True
        >>> is_bool(0)
        False
        >>> isinstance(True, int)
        True
    """
    return isinstance(value, (bool, np.bool_))


def is_iterable(value: t.Any) -> bool:
    """Return True if the object is iterable.

    In Python, there are three ways in which objects can be iterable:

    - they are registered as subclasses of `~collections.abc.Iterable`;
    - they provide a method `~object.__iter__()`;
    - they provide a method `~object.__getitem__()` and do not inherit
      from `dict`.

    In the latter case, the object must honor the sequence protocol: its
    `__getitem__()` must be callable with consecutive integers starting
    at 0 until it raises an `IndexError`.

    Example:

        >>> is_iterable([])
        True
        >>> is_iterable(0)
        False
        >>> is_iterable({})
        True
        >>> class Foo:
        ...     def __getitem__(self, i):
        ...         if i < 5:
        ...             return 2 * i
        ...         raise IndexError(i)
        >>> is_iterable(Foo())
        True
        >>> list(Foo())
        [0, 2, 4, 6, 8]
        >>> class Bar: pass
        >>> is_iterable(Bar())
        False
        >>> from collections.abc import Iterable
        >>> _ = Iterable.register(Bar)
        >>> is_iterable(Bar())
        True
    """
    return isinstance(value, t.Iterable) or hasattr(type(value), "__getitem__")


def is_box(space: gym.Space) -> tx.TypeGuard[gym.spaces.Box]:
    """Return True if the given space is a Box."""
    return isinstance(space, gym.spaces.Box)
