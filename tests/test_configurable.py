"""Test the Configurable API."""

# pylint: disable = missing-class-docstring, missing-function-docstring

import math

import pytest

from cernml.coi import BadConfig, Config


def test_bare_field() -> None:
    config = Config().add("foo", "bar")
    assert config.validate("foo", "bar") == "bar"
    assert config.validate("foo", "") == ""


def test_choice() -> None:
    config = Config().add("foo", "bar", choices=["bar", "baz"])
    assert config.validate("foo", "bar") == "bar"
    assert config.validate("foo", "baz") == "baz"
    with pytest.raises(BadConfig):
        config.validate("foo", "bam")


def test_int() -> None:
    config = Config().add("foo", 7)
    assert config.validate("foo", "7") == 7
    assert config.validate("foo", "-3") == -3
    assert config.validate("foo", "42_123") == 42_123
    with pytest.raises(BadConfig):
        config.validate("foo", "bar")
    with pytest.raises(BadConfig):
        config.validate("foo", "1.3")


def test_int_range() -> None:
    config = Config().add("foo", 0, range=(-10, 10))
    assert config.validate("foo", "-3") == -3
    for i in range(-10, 11):
        assert config.validate("foo", str(i)) == i
    with pytest.raises(BadConfig):
        config.validate("foo", "-11")
    with pytest.raises(BadConfig):
        config.validate("foo", "11")
    with pytest.raises(BadConfig):
        config.validate("foo", "10000")


def test_int_choice() -> None:
    config = Config().add("foo", 0, choices=range(1, 4))
    assert config.validate("foo", "3") == 3
    assert config.validate("foo", "2") == 2
    assert config.validate("foo", "1") == 1
    with pytest.raises(BadConfig):
        config.validate("foo", "0")


def test_float() -> None:
    config = Config().add("foo", 1.3)
    assert config.validate("foo", "1.3") == 1.3
    assert config.validate("foo", "-3") == -3
    assert config.validate("foo", "1e23") == 1e23
    assert config.validate("foo", "-inf") == -float("inf")
    assert math.isnan(config.validate("foo", "nan"))
    with pytest.raises(BadConfig):
        config.validate("foo", "bar")


def test_float_range() -> None:
    config = Config().add("foo", 1.0, range=(0.0, 2.0))
    assert config.validate("foo", "1.3") == 1.3
    assert config.validate("foo", "0") == 0.0
    assert config.validate("foo", "2") == 2.0
    with pytest.raises(BadConfig):
        config.validate("foo", "2.000001")
    with pytest.raises(BadConfig):
        config.validate("foo", "-1e-34")
    with pytest.raises(BadConfig):
        config.validate("foo", "nan")
    with pytest.raises(BadConfig):
        config.validate("foo", "inf")


def test_float_range_half_open() -> None:
    config = Config().add("foo", 1.0, range=(0.0, float("inf")))
    assert config.validate("foo", "1000.0") == 1000.0
    assert config.validate("foo", "inf") == float("inf")
    with pytest.raises(BadConfig):
        assert config.validate("foo", "-inf")
    with pytest.raises(BadConfig):
        assert config.validate("foo", "nan")


def test_int_range_half_open() -> None:
    config = Config().add("foo", 1, range=(0.0, float("inf")))
    assert config.validate("foo", "1000") == 1000
    with pytest.raises(BadConfig):
        assert config.validate("foo", "-inf")
    with pytest.raises(BadConfig):
        assert config.validate("foo", "3.0")


def test_bool() -> None:
    config = Config().add("foo", False)
    assert config.validate("foo", "1000") is True
    assert config.validate("foo", "check") is True
    assert config.validate("foo", "False") is True
    assert config.validate("foo", "") is False


def test_custom_type() -> None:
    def even_number(string: str) -> int:
        number = int(string)
        if number % 2:
            raise ValueError("not an even number: " + repr(string))
        return number

    config = Config().add("foo", 0, type=even_number)
    assert config.validate("foo", "0") == 0
    assert config.validate("foo", "2") == 2
    assert config.validate("foo", "4") == 4
    with pytest.raises(BadConfig):
        assert config.validate("foo", "bar")
    with pytest.raises(BadConfig):
        assert config.validate("foo", "1")


def test_validate_all() -> None:
    config = Config().add("foo", 0).add("bar", "a", choices=list("abc"))
    values = config.validate_all({"foo": "10", "bar": "b"})
    assert values.foo == 10
    assert values.bar == "b"
    with pytest.raises(BadConfig):
        config.validate_all({"foo": "nan", "bar": "b"})
    with pytest.raises(BadConfig):
        config.validate_all({"foo": "0", "bar": "d"})
    with pytest.raises(BadConfig):
        config.validate_all({"foo": "0"})
    with pytest.raises(BadConfig):
        config.validate_all({"foo": "0", "bar": "a", "baz": ""})
