# SPDX-FileCopyrightText: 2020 - 2024 CERN
# SPDX-FileCopyrightText: 2023 - 2024 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

"""These classes provide an interface for GUI configurability.

.. currentmodule:: cernml.coi

Some `Problem` classes have several parameters that determine certain
details of how they are solved, e.g. the bounds within which to search,
or a subset of parameters which are to be optimized.

These parameters are often set through the initializer method
:meth:`~object.__init__()`. However, this can usually not well be
annotated with limits, invariants, or other metadata.

The `Configurable` interface provides a uniform way for problem authors
to declare which parameters of their class are configurable and what
each parameter's invariants are. It's implemented as follows:

1. Define your configurable parameters in :meth:`~object.__init__()`.
2. Implement `~Configurable.get_config()` and return a `Config` object.
   This declares your configurable parameters and their invariants.
3. Implement `~Configurable.apply_config()`, which receives
   a `ConfigValues` object. Transfer each value into your object. Apply
   any further checks and raise an exception if any fail.
"""

from __future__ import annotations

import typing
from abc import abstractmethod
from collections import OrderedDict
from dataclasses import dataclass
from functools import singledispatch
from types import SimpleNamespace

import numpy as np

__all__ = (
    "BadConfig",
    "Config",
    "ConfigValues",
    "Configurable",
    "DuplicateConfig",
    "StrSafeBool",
    "deduce_type",
)

T = typing.TypeVar("T")

ConfigValues = SimpleNamespace


class DuplicateConfig(Exception):
    """Attempted to add two configs with the same name."""


class BadConfig(Exception):
    """A configuration value failed the validation."""


class Config:
    """Declaration of configurable parameters.

    This is the return type of `~Configurable.get_config()`. It is used
    by environments to *declare* their configurable parameters,
    including each parameter's validity invariants. This makes it
    possible for users of the environment to automatically generate an
    interface that prevents invalid values as early as possible.

    Usage example:

        >>> config = Config()
        >>> config
        <Config: []>
        >>> config.add("foo", 3).add("bar", 4)
        <Config: ['foo', 'bar']>
        >>> values = config.validate_all({"foo": "3", "bar": "4"})
        >>> values.foo
        3
        >>> config.validate_all({"foo": "a"})
        Traceback (most recent call last):
        ...
        BadConfig: invalid value for foo: 'a'
        >>> config.add("foo", 0)
        Traceback (most recent call last):
        ...
        DuplicateConfig: foo
    """

    @dataclass(frozen=True)
    class Field(typing.Generic[T]):
        """A single configurable field.

        This class is created exclusively via `.Config.add()`. It is
        a dataclass, so constructor parameters are also available as
        public fields.

            >>> config = Config().add("foo", 1.0)
            >>> fields = {field.dest: field for field in config.fields()}
            >>> fields["foo"].value
            1.0
            >>> fields["foo"].value = 2.0
            Traceback (most recent call last):
            ...
            dataclasses.FrozenInstanceError: cannot assign to field 'value'
        """

        # pylint: disable = too-many-instance-attributes

        dest: str
        value: T
        label: str
        help: str | None
        type: typing.Callable[[str], T]
        range: tuple[T, T] | None
        choices: tuple[T, ...] | None
        default: T | None

        def validate(self, text_repr: str) -> T:
            """Validate a user-chosen value.

            Args:
                text_repr: The string input to validate.

            Returns:
                The validated and converted value.

            Raises:
                `BadConfig`: if the value is invalid. If the field's
                    `type <.Config.add()>` raised an exception, it is
                    attached as the `~BaseException.__cause__` of this
                    exception.
            """
            try:
                value = self.type(text_repr)
                self._validate_range(value)
                self._validate_choices(value)
            except Exception as exc:
                raise BadConfig(
                    f"invalid value for {self.dest}: {text_repr!r}"
                ) from exc
            return value

        def _validate_range(self, value: T) -> None:
            if self.range is not None:
                low, high = self.range
                if not low <= value <= high:  # type: ignore[operator]
                    raise ValueError(f"{value} not in range [{low}, {high}]")

        def _validate_choices(self, value: T) -> None:
            if self.choices is not None and value not in self.choices:
                raise ValueError(f"{value} not in {self.choices!r}")

    def __init__(self) -> None:
        self._fields: dict[str, Config.Field] = OrderedDict()

    def __repr__(self) -> str:
        return f"<{type(self).__name__}: {list(self._fields)}>"

    def fields(self) -> typing.Iterable[Field]:
        """Return a read-only view of all declared fields."""
        return self._fields.values()

    def get_field_values(self) -> dict[str, typing.Any]:
        """Return a `dict` of the pre-configured field values.

        Note that this is not quite the expected input to
        `validate_all()`; the latter expects the dict values to be
        strings:

            >>> c = Config().add("flag", False).add("count", 10)
            >>> vars(c.validate_all({"flag": "False", "count": "10"}))
            {'flag': False, 'count': 10}

        Nonetheless, passing this dict to `validate_all()` may
        accidentally work, even though the type signatures don't match:

            >>> vars(c.validate_all(c.get_field_values()))
            {'flag': False, 'count': 10}
        """
        return {dest: field.value for dest, field in self._fields.items()}

    def add(
        self,
        dest: str,
        value: T,
        *,
        label: str | None = None,
        help: str | None = None,
        type: typing.Callable[[str], T] | None = None,
        range: tuple[T, T] | None = None,
        choices: typing.Sequence[T] | None = None,
        default: T | None = None,
    ) -> "Config":
        """Add a new config field.

        Args:
            dest: The name of the configurable parameter being declared.
                This is the name under which the value will be available
                in `~Configurable.apply_config()`.
            value: The value to initialize this parameter with.
                Typically, this is the current setting for this field.
            label: If passed, the name under which the parameter will be
                shown to the user. If not passed, *dest* is used.
            help: If passed, a string that further explains this
                configurable parameter. In contrast to *label*, this may
                be one or more sentences.
            type: If passed, a function that type-checks the user input
                and converts it to the same type as *value*. This should
                raise an exception if the given input is invalid. If not
                passed, the result of calling
                `~configurable.deduce_type()` on the given *value* is
                used.
            range: If passed, a tuple (*low*, *high*) of limits between
                which the user-chosen value must lie. The interval is
                closed, i.e. exact values of *low* or *high* are
                accepted.
            choices: If passed, a list of values of the same type as
                *value*. A user-chosen value for this field must be in
                this list.
            default: If passed, a default value that the user should be
                able to easily reset this field to. This is preferrable
                if there is a single obvious choice for this field.

        Returns:
            This object itself, to allow method-chaining_.

        Raises:
            DuplicateConfig: if a config parameter with this *dest*
                value has already been declared.
            TypeError: if both *range* and *choices* are passed.

        .. _method-chaining:
            https://en.wikipedia.org/wiki/Method_chaining
        """
        # pylint: disable = redefined-builtin
        if dest in self._fields:
            raise DuplicateConfig(dest)
        if label is None:
            label = dest
        if type is None:
            type = deduce_type(value)
        if range is not None and choices is not None:
            raise TypeError("cannot pass both `range` and `choices`")
        if choices is not None:
            choices = tuple(choices)
        self._fields[dest] = self.Field(
            dest,
            value=value,
            label=label,
            help=help,
            type=type,
            range=range,
            choices=choices,
            default=default,
        )
        return self

    def extend(self, other: "Config") -> "Config":
        """Add all fields of another config to this one.

        Args:
            other: Another `Config` object from which to copy
                each field in sequence.

        Returns:
            This config object itself to allow method-chaining.

        Raises:
            DuplicateConfig: if *other* contains a config parameter with
                the same *dest* value as a parameter in this config.

        Example:

            >>> first = Config().add("first", 0.0)
            >>> second = Config().add("second", 0.0)
            >>> first.extend(second)
            <Config: ['first', 'second']>
            >>> first.extend(second)
            Traceback (most recent call last):
            ...
            DuplicateConfig: {'second'}
        """
        duplicates = self._fields.keys() & other._fields.keys()
        if duplicates:
            raise DuplicateConfig(duplicates)
        self._fields.update(other._fields)
        return self

    def validate(self, name: str, text_repr: str) -> typing.Any:
        """Validate a user-chosen value.

        Args:
            name: The name of the configurable field. This is the same
                as the *dest* parameter of `add()`.
            text_repr: The string input to validate.

        Returns:
            The validated and converted value.

        Raises:
            BadConfig: if the value is invalid. If the field's `type
                <add()>` raised an exception, it is attached as the
                `~BaseException.__cause__` of this exception.
        """
        return self._fields[name].validate(text_repr)

    def validate_all(self, values: typing.Mapping[str, str]) -> "ConfigValues":
        """Validate user-chosen set of configurations.

        Args:
            values: A mapping from `dest <add()>` names to unparsed
                string values. This must have *exactly* one item for
                every configurable field. Neither missing nor excess
                items are allowed.

        Returns:
            A namespace with the validated and converted values as
            attributes.

        Raises:
            BadConfig: if one of the values is invalid, if there are too
                many items or if an item is missing. If a field's `type
                <add()>` raised an exception, it is attached as the
                `~BaseException.__cause__` of this exception.
        """
        values = dict(values)  # Make a copy, we want to manipulate it.
        result = ConfigValues()
        for dest in self._fields:
            try:
                value = values.pop(dest)
            except KeyError as exc:
                raise BadConfig(f"missing config: {dest!r}") from exc
            value = self.validate(dest, value)
            setattr(result, dest, value)
        if values:
            raise BadConfig(f"unknown configs: {list(values)!r}")
        return result


@typing.runtime_checkable
class Configurable(typing.Protocol):
    """Interface for problems that are configurable.

    This protocol is defined by two methods: `get_config()` and
    `apply_config()`. Because it is a protocol, you need not inherit
    from it to implement its interface:

        >>> class VirtualSubclass:
        ...     def get_config(self):
        ...         return Config()
        ...     def apply_config(self, values):
        ...         pass
        >>> issubclass(VirtualSubclass, Configurable)
        True
        >>> issubclass(int, Configurable)
        False
    """

    @abstractmethod
    def get_config(self) -> Config:
        """Return a declaration of configurable parameters."""

    @abstractmethod
    def apply_config(self, values: ConfigValues) -> None:
        """Configure this object using the given values.

        The *values* have already been validated using the information
        given in `get_config()`, but this method may apply further
        checks.

        This method should be *transactional*, i.e. in the case of
        failure, an effort should be made that none of the values are
        applied.

        Args:
            values: A namespace with one attribute for each field
                declared in `get_config()`. The attribute name is
                exactly the *dest* parameter of `Config.add()`.

        Raises:
            Exception: If any additional validation checks fail.
        """


AnyBool = typing.TypeVar("AnyBool", bool, np.bool_)


class StrSafeBool(typing.Generic[AnyBool]):
    """String-safe wrapper around Boolean types.

    Integers round-trip through string conversion:

        >>> int(str(123))
        123

    Booleans, however, do not:

        >>> bool(str(True))
        True
        >>> bool(str(False))
        True

    This wrapper special-cases the strings ``"True"`` and ``"False"``
    and replaces them with the built-in Boolean values `True` and
    `False`:

        >>> sbool = StrSafeBool(bool)
        >>> sbool # doctest: +ELLIPSIS
        <...StrSafeBool(<class 'bool'>)>
        >>> sbool(str(True))
        True
        >>> sbool(str(False))
        False

    This special case is case-sensitive:

        >>> sbool("False")
        False
        >>> sbool("false")
        True

    You usually don't interact with this wrapper directly. It is used
    internally by `.Config.Field` as a default value for the *type*
    argument in case the *value* is a Boolean.
    """

    __slots__ = ("base_type",)

    def __init__(self, base_type: type[AnyBool]) -> None:
        self.base_type: type[AnyBool] = base_type

    def __repr__(self) -> str:
        return f"<{type(self).__module__}.{type(self).__name__}({self.base_type!r})>"

    def __call__(self, text_repr: str, /) -> AnyBool:
        """Coerce the given string to the chosen boolean type.

        The exact strings ``"True"`` and ``"False"`` are converted to
        the True and False value of the chosen boolean type. This is
        case-sensitive. Any other string is passed directly to the
        boolean constructor.

            >>> b = StrSafeBool(repr)
            >>> b('1')
            "'1'"
            >>> b('yes')
            "'yes'"
            >>> b('true')
            "'true'"
            >>> b('True')
            'True'
        """
        if isinstance(text_repr, str):
            if text_repr == "True":
                return self.base_type(True)
            if text_repr == "False":
                return self.base_type(False)
        return self.base_type(text_repr)


@singledispatch
def deduce_type(value: typing.Any, /) -> typing.Callable[[str], typing.Any]:
    """For a given `~.Config.Field` *value*, deduce the correct *type*.

    If you don't pass an explicit *type* to `.Config.add()`, this
    function determines it based on the *value*. In almost all cases,
    this simply returns :samp:`type(value)`. However, in the case of
    `bool` and `numpy.bool_`, a special wrapper `StrSafeBool` is
    returned. This wrapper ensures that
    :samp:`deduce_type({bool})(str({bool}))` round-trips correctly:

        >>> sbool = deduce_type(np.bool_(True))
        >>> sbool  # doctest: +ELLIPSIS
        <...StrSafeBool(<class 'numpy.bool_'>)>
        >>> sbool(str(True))
        True
        >>> sbool(str(False))
        False

    The naive choice would produce the wrong result for `False` because
    ``bool("False")`` actually tests whether the string ``"False"`` is
    empty:

        >>> bool(str(True))
        True
        >>> bool(str(False))
        True

    This function uses `~functools.singledispatch`, so you can add your
    own special-cases:

        >>> class Point:
        ...     def __init__(self, x, y):
        ...         self.x, self.y = x, y
        ...     def __repr__(self):
        ...         return f"({self.x}; {self.y})"
        ...     @classmethod
        ...     def fromstr(cls, s):
        ...         if (s[0], s[-1]) != ("(", ")"):
        ...             raise ValueError(f"not a point: {s!r}")
        ...         s = s[1:-1]
        ...         x, y = (float(c.strip()) for c in s.split(";"))
        ...         return cls(x, y)
        ...
        >>> @deduce_type.register(Point)
        ... def _(p):
        ...     return type(p).fromstr
        ...
        >>> p = Point(1.0, 2.0)
        >>> deduce_type(p)(str(p))
        (1.0; 2.0)
    """
    return type(value)


@deduce_type.register
def _(value: bool, /) -> StrSafeBool[bool]:
    return StrSafeBool(type(value))


@deduce_type.register
def _(value: np.bool_, /) -> StrSafeBool[np.bool_]:
    return StrSafeBool(type(value))
