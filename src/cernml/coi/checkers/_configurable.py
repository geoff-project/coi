"""Checker for the `Configurable` ABC."""

import os
import typing as t
import warnings
from unittest.mock import Mock, PropertyMock

import numpy as np

from .._configurable import Config, Configurable


def check_configurable(problem: Configurable, warn: bool = True) -> None:
    """Check the run-time invariants of the given interface."""
    config = problem.get_config()
    assert_is_good_config(config, warn)
    assert_handles_values(problem, config, warn)


def assert_is_good_config(config: Config, warn: bool = True) -> None:
    """Check that the given Config has good types.

    >>> from warnings import simplefilter
    >>> simplefilter("error")
    >>> assert_is_good_config(True)
    Traceback (most recent call last):
    ...
    AssertionError: result of get_config() must be a Config: True
    >>> good_config = Config().add("foo", 0)
    >>> assert_is_good_config(good_config)
    >>> bad_config = Config().add("foo", [])
    >>> assert_is_good_config(bad_config)
    Traceback (most recent call last):
    ...
    UserWarning: value [] of field 'foo' has unusual ...
    >>> assert_is_good_config(bad_config, warn=False)
    >>> bad_config = Config().add("foo", 0, default=[])
    >>> assert_is_good_config(bad_config)
    Traceback (most recent call last):
    ...
    UserWarning: default [] of field 'foo' has unusual ...
    >>> assert_is_good_config(bad_config, warn=False)
    """
    assert isinstance(
        config, Config
    ), f"result of get_config() must be a Config: {config!r}"
    if warn:
        warning_template = (
            "{kind} {value!r} of field {dest!r} has unusual "
            "type {value.__class__!r}; config editors might be "
            "unable to handle it"
        )
        good_types = (
            bool,
            int,
            float,
            str,
            os.PathLike,
            np.bool_,
            np.integer,
            np.floating,
        )
        for field in config.fields():
            if not isinstance(field.value, good_types):
                warnings.warn(
                    warning_template.format(
                        kind="value", value=field.value, dest=field.dest
                    )
                )
            if field.default is not None and not isinstance(field.default, good_types):
                warnings.warn(
                    warning_template.format(
                        kind="default", value=field.default, dest=field.dest
                    )
                )


def assert_handles_values(
    problem: Configurable, config: Config, warn: bool = True
) -> None:
    """Check that the current config values can be applied.

    >>> from warnings import simplefilter
    >>> simplefilter("error")
    >>> config = Config().add("foo", 0)
    >>> class GoodConfigurable:
    ...     def apply_config(self, values):
    ...         self.foo = values.foo
    >>> assert_handles_values(GoodConfigurable(), config)
    >>> class AccessNonexisting:
    ...     def apply_config(self, values):
    ...         self.bar = values.bar
    >>> assert_handles_values(AccessNonexisting(), config)
    Traceback (most recent call last):
    ...
    AttributeError: ...
    >>> class ForgetToAccess:
    ...     def apply_config(self, values): pass
    >>> assert_handles_values(ForgetToAccess(), config)
    Traceback (most recent call last):
    ...
    UserWarning: configured value for field 'foo' has not been ...
    >>> assert_handles_values(ForgetToAccess(), config, warn=False)
    """
    values = make_mock_values(config)
    problem.apply_config(values)
    if warn:
        # Dict access to get the underlying properties. Note that
        # because this is a mock, type(values) != values.__class__.
        property_mocks = vars(values.__class__)
        for field in config.fields():
            prop: PropertyMock = property_mocks[field.dest]
            if not prop.call_count:
                warnings.warn(
                    f"configured value for field {field.dest!r} has "
                    f"not been read in apply_config()"
                )


def make_mock_values(config: Config) -> Mock:
    """Create a mock of the validated config values.

    Example:

        >>> config = Config().add("foo", "left").add("bar", "right")
        >>> values = make_mock_values(config)


    Getting an attribute is logged:

        >>> vars(values.__class__)['foo'].call_args_list
        []
        >>> values.foo
        'left'
        >>> vars(values.__class__)['foo'].call_args_list
        [call()]

    Setting an attribute is logged as well:

        >>> values.bar
        'right'
        >>> values.bar = 'RIGHT'
        >>> vars(values.__class__)['bar'].call_args_list
        [call(), call('RIGHT')]

    Unconfigured attributes cannot be accessed:

        >>> values.baz
        Traceback (most recent call last):
        ...
        AttributeError: Mock object has no attribute 'baz'
        >>> values.baz = 3
        Traceback (most recent call last):
        ...
        AttributeError: Mock object has no attribute 'baz'
    """
    strings = {f.dest: get_round_tripping_string_repr(f.value) for f in config.fields()}
    values = config.validate_all(strings)

    class SubMock(Mock):
        """Subclass of `Mock` that isolates property mocks."""

    for dest, value in vars(values).items():
        prop = PropertyMock(return_value=value)
        setattr(SubMock, dest, prop)
    result = SubMock(spec_set=SubMock)
    # The mere use of `spec_set` already accesses our properties, so we
    # must reset them manually.
    for dest in vars(values):
        # Dict access to get the underlying properties.
        vars(SubMock)[dest].reset_mock()
    return result


def get_round_tripping_string_repr(value: t.Any) -> str:
    """Get a string representation that roundtrips well.

    This is basically `str()` with a special case for boolean
    types so that ``bool(str(False)) is False``.

    >>> get_round_tripping_string_repr([1, 2, 3])
    '[1, 2, 3]'
    >>> get_round_tripping_string_repr(True)
    'True'
    >>> get_round_tripping_string_repr(False)
    ''
    """
    if isinstance(value, (bool, np.bool_)):
        return "True" if value else ""
    return str(value)
