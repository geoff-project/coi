#!/usr/bin/env python
"""Provide `Configurable`, an interface for GUI compatibility."""

from abc import ABCMeta, abstractmethod
from collections import OrderedDict
from types import SimpleNamespace
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Mapping,
    NamedTuple,
    Optional,
    Sequence,
    Tuple,
)

from ._abc_helpers import check_methods as _check_methods


class DuplicateConfig(Exception):
    """Attempted to add two configs with the same name."""


class BadConfig(Exception):
    """A configuration value failed the validation."""


class Config:
    """Declaration of configurable parameters.

    This is the expected return type of `Configurable.get_config()`. It
    is used by environments to *declare* their configurable parameters,
    including each parameter's validity invariants. This makes it
    possible for users of the environment to automatically generate an
    interface that prevents invalid values as early as possible.

    For more information, see `Configurable`.

    Usage:

        >>> config = Config()
        >>> config
        <Config: []>
        >>> config.add('foo', 3)
        <Config: ['foo']>
        >>> values = config.validate_all({'foo': '3'})
        >>> values.foo
        3
        >>> config.validate_all({'foo': 'a'})
        Traceback (most recent call last):
        ...
        coi._configurable.BadConfig: invalid value for foo: 'a'
    """

    # Note: Once Python 3.6 support is dropped, this should subclass
    # NamedTuple _and_ Generic[T].
    class Field(NamedTuple):
        """A single configurable field.

        Don't instantiate this class yourself. Use `Config.add()`
        instead.
        """

        dest: str
        value: Any
        label: str
        help: Optional[str]
        type: Callable[[str], Any]
        range: Optional[Tuple[Any, Any]]
        choices: Optional[List[Any]]
        default: Optional[Any]

        def validate(self, text_repr: str) -> Any:
            """Validate a user-chosen value.

            Args:
                text_repr: The string input to validate.

            Returns:
                The validated and converted value.

            Raises:
                BadConfig if the value could not be validated.
            """
            try:
                value: Any = self.type(text_repr)
                if self.range is not None:
                    low, high = self.range
                    if not low <= value <= high:
                        raise ValueError(f"{value} not in range [{low}, {high}]")
                if self.choices is not None:
                    if not value in self.choices:
                        raise ValueError(f"{value} not in {self.choices!r}")
            except Exception as exc:
                raise BadConfig(
                    f"invalid value for {self.dest}: {text_repr!r}"
                ) from exc
            return value

    def __init__(self) -> None:
        self._fields: Dict[str, Config.Field] = OrderedDict()

    def __repr__(self) -> str:
        return f"<{type(self).__name__}: {list(self._fields)}>"

    def fields(self) -> Iterable[Field]:
        """Return a read-only view of all declared fields."""
        return self._fields.values()

    def add(
        self,
        dest: str,
        value: Any,
        *,
        label: Optional[str] = None,
        help: Optional[str] = None,
        type: Optional[Callable[[str], Any]] = None,
        range: Optional[Tuple[Any, Any]] = None,
        choices: Optional[Sequence[Any]] = None,
        default: Optional[Any] = None,
    ) -> "Config":
        """Add a new config field.

        Args:
            dest: The name of the configurable parameter being declared.
                This is the name under which the value will be available
                in `Configurable.apply_config()`.
            value: The value to initialize this parameter with.
                Typically, this is the current setting for this field.
            label: The display name of the parameter. This will be
                displayed to the user, if possible. If not passed,
                `dest` is reused.
            help: A string that further explains this configurable
                parameter. A GUI might e.g. present this string as a
                tooltip.
            type: A function used for type-checking and conversion. This
                function should take a string and produce a value of the
                same type as `value`. It will be applied to any user
                input that produces a new configuration. If the given
                string is not a valid input, this function should raise
                an exception. If not passed, this is simply the type of
                `value`, e.g. `int`, `float`, etc.
            range: If passed, must be a tuple `(low, high)`. A
                user-chosen value for this field must be within the
                closed interval described by these values.
            choices: If passed, must be a list of values of the same
                type as `value`. A user-chosen value for this field must
                be one of this list.
            default: If passed, a default value that the user should be
                able to easily reset this field to. This is preferrable
                if there is a single obvious choice for this field.
        """
        # pylint: disable = redefined-builtin
        if dest in self._fields:
            raise DuplicateConfig(dest)
        if label is None:
            label = dest
        if type is None:
            type = value.__class__
        if range is not None and choices is not None:
            raise ValueError("cannot pass both `range` and `choices`")
        if choices is not None:
            choices = list(choices)
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

    def validate(self, name: str, text_repr: str) -> Any:
        """Validate a user-chosen value.

        Args:
            name: The name of the configurable field. This is the same
                as the `dest` parameter of `Config.add()`.
            text_repr: The string input to validate.

        Returns:
            The validated and converted value.

        Raises:
            BadConfig if the value could not be validated.
        """
        return self._fields[name].validate(text_repr)

    def validate_all(self, values: Mapping[str, str]) -> SimpleNamespace:
        """Validate user-chosen set of configurations.

        Args:
            values: The mapping `dest` to unparsed string values. This
                must have exactly one item for every configurable field.
                Neither missing nor excess items are allowed.

        Returns:
            A namespace containing the validated and converted values as
            attributes.

        Raises:
            BadConfig if a field fails to validate, if `values` has too
                many items or if it misses an item.
        """
        values = dict(values)  # Make a copy, we want to manipulate it.
        result = SimpleNamespace()
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


class Configurable(metaclass=ABCMeta):
    """Interface for problems that are configurable.

    Some `SingleOptimizable` or `Env` problems have several parameters
    that determine certain details of how they are solved. A classic
    configurable parameter of environments is the reward objective, i.e.
    the minimum step reward upon which an episode is considered solved.

    While these parameters can be set through the initializer, this has
    the problem that it is difficult to annotate them with limits,
    invariants, etc.

    For this reason, this interface provides a uniform way for problem
    authors to declare which parameters of their class are configurable
    and what each parameter's invariants are. Its usage is extremely
    trivial. The `get_config()` method returns a declaration of
    configurable aprameters, the `apply_config()` takes a collection of
    configurations and applies them to the problem. At any point of the
    update, an exception may be raised to signal that an invariant has
    been violated.

    Usage example:

        >>> class ExampleEnv(Configurable):
        ...     def __init__(self):
        ...         self.action_scale = 1.0
        ...     def get_config(self):
        ...         config = Config()
        ...         config.add(
        ...             'action_scale',
        ...             self.action_scale,
        ...             label='Action scale (mrad)',
        ...             range=(0.0, 2.0),
        ...             default=1.0,
        ...             )
        ...         return config
        ...     def apply_config(self, values):
        ...         self.action_scale = values.action_scale
        >>> issubclass(ExampleEnv, Configurable)
        True

    This is an abstract base class. You need not inherit from it to
    implement its interface:

        >>> class AbstractChild:
        ...     def get_config(self):
        ...         return Config()
        ...     def apply_config(self, values):
        ...         pass
        >>> issubclass(AbstractChild, Configurable)
        True
        >>> issubclass(int, Configurable)
        False
    """

    @abstractmethod
    def get_config(self) -> Config:
        """Return a declaration of configurable parameters."""

    @abstractmethod
    def apply_config(self, values: SimpleNamespace) -> None:
        """Configure this object using the given values.

        The `values` must have already been validated using the
        information given in `get_config()`, but this method may apply
        further checks. If validation fails, this method may raise an
        exception.

        This method is atomic, i.e. in the case of failure, no value at
        all is applied.

        Args:
            values: A namespace object. It must have one attribute for
                each field declared in `get_config()`. The attribute
                name is exactly the `dest` parameter of `Config.add()`.
        """

    @classmethod
    def __subclasshook__(cls, other: type) -> Any:
        if cls is Configurable:
            return _check_methods(other, "get_config", "apply_config")
        return NotImplemented
