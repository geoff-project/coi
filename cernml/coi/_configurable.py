"""Provide :class:`Configurable`, an interface for GUI compatibility."""

import typing as t
from abc import ABCMeta, abstractmethod
from collections import OrderedDict
from dataclasses import dataclass
from types import SimpleNamespace

from ._abc_helpers import check_methods as _check_methods

T = t.TypeVar("T")  # pylint: disable = invalid-name
T.__module__ = ""


class DuplicateConfig(Exception):
    """Attempted to add two configs with the same name."""


class BadConfig(Exception):
    """A configuration value failed the validation."""


class Config:
    """Declaration of configurable parameters.

    This is the return type of :meth:`Configurable.get_config()`. It is
    used by environments to *declare* their configurable parameters,
    including each parameter's validity invariants. This makes it
    possible for users of the environment to automatically generate an
    interface that prevents invalid values as early as possible.

    For more information, see :class:`Configurable`.

    Usage:

        >>> config = Config()
        >>> config
        <Config: []>
        >>> config.add("foo", 3)
        <Config: ['foo']>
        >>> values = config.validate_all({"foo": "3"})
        >>> values.foo
        3
        >>> config.validate_all({"foo": "a"})
        Traceback (most recent call last):
        ...
        coi._configurable.BadConfig: invalid value for foo: 'a'
        >>> config.add("foo", 0)
        Traceback (most recent call last):
        ...
        coi._configurable.DuplicateConfig: foo

    If your class consists of multiple configurable components, you can
    combine their individual configs as long as the names don't overlap:

        >>> class Kicker(Configurable):
        ...     def __init__(self) -> None:
        ...         self.scale = 0.1
        ...     def get_config(self) -> Config:
        ...         return Config().add("scale", self.scale)
        ...     def apply_config(self, values: SimpleNamespace) -> None:
        ...         self.scale = values.scale
        >>> class LossMonitor(Configurable):
        ...     def __init__(self) -> None:
        ...         self.min_reading = 1.0
        ...     def get_config(self) -> Config:
        ...         return Config().add("min_reading", self.min_reading)
        ...     def apply_config(self, values: SimpleNamespace) -> None:
        ...         self.min_reading = values.min_reading
        >>> class Problem(Configurable):
        ...     def __init__(self) -> None:
        ...         self.kicker = Kicker()
        ...         self.monitor = LossMonitor()
        ...     def get_config(self) -> Config:
        ...         return (
        ...             Config()
        ...             .extend(self.kicker.get_config())
        ...             .extend(self.monitor.get_config())
        ...         )
        ...     def apply_config(self, values: SimpleNamespace):
        ...         self.kicker.apply_config(values)
        ...         self.monitor.apply_config(values)
        >>> problem = Problem()
        >>> config = problem.get_config()
        >>> config
        <Config: ['scale', 'min_reading']>
        >>> values = {'scale': 0.0, 'min_reading': 0.0}
        >>> values = config.validate_all(values)
        >>> problem.apply_config(values)
        >>> problem.kicker.scale
        0.0
        >>> problem.monitor.min_reading
        0.0
    """

    @dataclass(frozen=True)
    class Field(t.Generic[T]):
        """A single configurable field.

        This class is created exclusively via
        :meth:`Config.add()<cernml.coi.Config.add>`. It is a dataclass,
        so constructor parameters are also available as public fields.

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
        help: t.Optional[str]
        type: t.Optional[t.Callable[[str], T]]  # /python/mypy/issues/9489
        range: t.Optional[t.Tuple[T, T]]
        choices: t.Optional[t.List[T]]
        default: t.Optional[T]

        def validate(self, text_repr: str) -> T:
            """Validate a user-chosen value.

            Args:
                text_repr: The string input to validate.

            Returns:
                The validated and converted value.

            Raises:
                :exc:`BadConfig`: if the value could not be
                    validated.
            """
            try:
                # Workaround for the following Mypy issue:
                # https://github.com/python/mypy/issues/9489
                assert self.type is not None
                value: t.Any = self.type(text_repr)
                if self.range is not None:
                    low, high = self.range
                    if not low <= value <= high:
                        raise ValueError(f"{value} not in range [{low}, {high}]")
                if self.choices is not None:
                    if value not in self.choices:
                        raise ValueError(f"{value} not in {self.choices!r}")
            except Exception as exc:
                raise BadConfig(
                    f"invalid value for {self.dest}: {text_repr!r}"
                ) from exc
            return value

    def __init__(self) -> None:
        self._fields: t.Dict[str, Config.Field] = OrderedDict()

    def __repr__(self) -> str:
        return f"<{type(self).__name__}: {list(self._fields)}>"

    def fields(self) -> t.Iterable[Field]:
        """Return a read-only view of all declared fields."""
        return self._fields.values()

    def add(
        self,
        dest: str,
        value: T,
        *,
        label: t.Optional[str] = None,
        help: t.Optional[str] = None,
        type: t.Optional[t.Callable[[str], T]] = None,
        range: t.Optional[t.Tuple[T, T]] = None,
        choices: t.Optional[t.Sequence[T]] = None,
        default: t.Optional[T] = None,
    ) -> "Config":
        """Add a new config field.

        Args:
            dest: The name of the configurable parameter being declared.
                This is the name under which the value will be available
                in :meth:`~Configurable.apply_config()`.
            value: The value to initialize this parameter with.
                Typically, this is the current setting for this field.
            label: The display name of the parameter. This will be
                displayed to the user. If not passed, *dest* is used.
            help: A string that further explains this configurable
                parameter. In contrast to *label*, this may be one or
                more sentences.
            type: A function that type-checks each user input (always a
                string) and converts it to the same type as *value*. If
                the given string is not a valid input, this function
                should raise an exception. If not passed, this is simply
                the type of *value*, e.g. :class`int`, :class:`float`,
                etc.
            range: If passed, must be a tuple (*low*, *high*). A
                user-chosen value for this field must be within the
                closed interval described by these values.
            choices: If passed, must be a list of values of the same
                type as *value*. A user-chosen value for this field must
                be one of this list.
            default: If passed, a default value that the user should be
                able to easily reset this field to. This is preferrable
                if there is a single obvious choice for this field.

        Returns:
            This config object itself to allow method-chaining.

        Raises:
            DuplicateConfig: if a config parameter with this *dest*
                value has already been declared.
            TypeError: if both *range* and *choices* are passed.
        """
        # pylint: disable = redefined-builtin
        if dest in self._fields:
            raise DuplicateConfig(dest)
        if label is None:
            label = dest
        if type is None:
            type = value.__class__
        if range is not None and choices is not None:
            raise TypeError("cannot pass both `range` and `choices`")
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

    def extend(self, other: "Config") -> "Config":
        """Add all fields of another config to this one.

        Args:
            other: Another :class:`Config` object from which to copy
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
            coi._configurable.DuplicateConfig: {'second'}
        """
        duplicates = self._fields.keys() & other._fields.keys()
        if duplicates:
            raise DuplicateConfig(duplicates)
        self._fields.update(other._fields)
        return self

    def validate(self, name: str, text_repr: str) -> t.Any:
        """Validate a user-chosen value.

        Args:
            name: The name of the configurable field. This is the same
                as the *dest* parameter of :meth:`add()`.
            text_repr: The string input to validate.

        Returns:
            The validated and converted value.

        Raises:
            BadConfig: if the value could not be validated.
        """
        return self._fields[name].validate(text_repr)

    def validate_all(self, values: t.Mapping[str, str]) -> SimpleNamespace:
        """Validate user-chosen set of configurations.

        Args:
            values: The mapping *dest* to unparsed string values. This
                must have exactly one item for every configurable field.
                Neither missing nor excess items are allowed.

        Returns:
            A namespace containing the validated and converted values as
            attributes.

        Raises:
            BadConfig: if a field fails to validate, if *values* has too
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

    Some :class:`Problem` classes have several parameters that determine
    certain details of how they are solved. A classic configurable
    parameter of environments is the *reward objective*, i.e. the
    minimum reward for a step upon which an episode is considered
    solved.

    While these parameters can be set through the initializer, this has
    the problem that it is difficult to annotate them with limits,
    invariants, etc.

    For this reason, this interface provides a uniform way for problem
    authors to declare which parameters of their class are configurable
    and what each parameter's invariants are. It is very easy to use for
    problem authors:

    1. Implement :meth:`get_config()` and return a declaration of
       configurable parameters. Certain invariants, limits, etc. may be
       declared for each parameter.
    2. Implement :meth:`apply_config()` which is given a collection of
       new configured values. Transfer each value into your object.
       Apply any further checks and raise an exception if any fail.

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
        ...         )
        ...         return config
        ...     def apply_config(self, values):
        ...         self.action_scale = values.action_scale
        >>> issubclass(ExampleEnv, Configurable)
        True

    A host application can use this interface as follows:

        >>> env = ExampleEnv()
        >>> config = env.get_config()
        >>> # Present configs to the user.
        >>> {field.dest: str(field.value) for field in config.fields()}
        {'action_scale': '1.0'}
        >>> # Transfer a user choice back to the env.
        >>> values = config.validate_all({"action_scale": "1.5"})
        >>> values
        namespace(action_scale=1.5)
        >>> env.apply_config(values)
        >>> env.action_scale
        1.5

    :class:`Configurable` is an :term:`abstract base class`. You need
    not inherit from it to implement its interface:

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
    def get_config(self) -> "Config":
        """Return a declaration of configurable parameters."""

    @abstractmethod
    def apply_config(self, values: SimpleNamespace) -> None:
        """Configure this object using the given values.

        The *values* have already been validated using the information
        given in :meth:`get_config()`, but this method may apply further
        checks.

        This method should be *transactional*, i.e. in the case of
        failure, an effort should be made that none of the values are
        applied.

        Args:
            values: A namespace object. It has one attribute for each
                field declared in :meth:`get_config()`. The attribute
                name is exactly the *dest* parameter of
                :meth:`Config.add()`.

        Raises:
            Exception: If any additional validation checks fail.
        """

    @classmethod
    def __subclasshook__(cls, other: type) -> t.Any:
        if cls is Configurable:
            return _check_methods(other, "get_config", "apply_config")
        return NotImplemented
