"""Checker for the `Configurable` ABC."""

import os
import typing as t
import warnings
from unittest.mock import Mock, PropertyMock

import numpy as np

from .._configurable import Config, Configurable


def check_configurable(problem: Configurable, warn: bool = True) -> None:
    """Check that an optimizable follows our conventions."""
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
        submock_class = values.__class__
        for field in config.fields():
            prop: PropertyMock = vars(submock_class)[field.dest]
            if not prop.call_count:
                warnings.warn(
                    f"configured value for field {field.dest!r} has "
                    f"not been read in apply_config()"
                )


def make_mock_values(config: Config) -> Mock:
    """Create a mock of the validated config values.

    >>> config = Config().add("foo", 0).add("bar", False)
    >>> values = make_mock_values(config)
    >>> values.foo
    0
    >>> vars(values.__class__)['foo'].call_args_list
    [call()]
    >>> values.bar
    False
    >>> values.bar = True
    >>> vars(values.__class__)['bar'].call_args_list
    [call(), call(True)]
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
        """Subclass of :class:`Mock` that isolates property mocks."""

    for dest, value in vars(values).items():
        prop = PropertyMock(return_value=value)
        setattr(SubMock, dest, prop)
    return SubMock(spec_set=SubMock)


def get_round_tripping_string_repr(value: t.Any) -> str:
    """Get a string representation that roundtrips well.

    This is basically :func:`str()` with a special case for boolean
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
