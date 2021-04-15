"""An enum of all the possible machines an environment can pertain to."""

import functools
import string
import typing as t
import warnings
from enum import Enum, EnumMeta


def _pascal_to_screaming_snake_case(word: str) -> str:
    result = [word[0].upper()]
    for char in word[1:]:
        if char not in string.ascii_lowercase:
            result.append("_")
        result.append(char.upper())
    return "".join(result)


T = t.TypeVar("T")  # pylint: disable=invalid-name


def _deprecate_pascal_case(
    func: t.Callable[[t.Type[T], str], T]
) -> t.Callable[[t.Type[T], str], T]:
    @functools.wraps(func)
    def _wrapper(cls: t.Type[T], name: str) -> T:
        if not name.isupper() and "_" not in name:
            good_name = _pascal_to_screaming_snake_case(name)
            warnings.warn(
                f"Machine.{name} is deprecated; please use {good_name} instead",
                DeprecationWarning,
                stacklevel=2,
            )
            name = good_name
        return func(cls, name)

    return _wrapper


class EnforceAllUpperCaseEnumNames(EnumMeta):
    """Enum metaclass that forbids PascalCase-style member names.

    This is a transitional feature to deprecate the following names:

    - coi.Machine.Linac2,
    - coi.Machine.Linac3,
    - coi.Machine.Linac4,
    - coi.Machine.NoMachine,
    - coi.Machine.Awake,
    - coi.Machine.Leir

    in favor of the new, all-upper-case names. It will issue a
    DeprecationWarning on each access of ``Machine["name"]`` or
    ``Machine.name`` or ``getattr(Machine, "name")`` where ``name`` is
    one of the deprecated names.
    """

    # typeshed does not acknowledge EnumMeta.__getattr__.
    __getattr__ = _deprecate_pascal_case(EnumMeta.__getattr__)  # type: ignore
    __getitem__ = _deprecate_pascal_case(EnumMeta.__getitem__)


class Machine(Enum, metaclass=EnforceAllUpperCaseEnumNames):
    """Enum of the various accelerators at CERN.

    This enum should be used by environments in their
    :attr:`~Problem.metadata` dictionary to declare which accelerator
    they pertain to. This can be used to filter a collection of
    environments for only those that are interesting to a certain group
    of operators.

    This list is intentionally left incomplete. If you wish to use this
    API at a machine that is not listed in this enum, please contact the
    developers to have it included.
    """

    NO_MACHINE = "no machine"
    LINAC_2 = "Linac2"
    LINAC_3 = "Linac3"
    LINAC_4 = "Linac4"
    LEIR = "LEIR"
    PS = "PS"  # pylint: disable=invalid-name
    PSB = "PSB"
    SPS = "SPS"
    AWAKE = "AWAKE"
    LHC = "LHC"
    ISOLDE = "ISOLDE"
